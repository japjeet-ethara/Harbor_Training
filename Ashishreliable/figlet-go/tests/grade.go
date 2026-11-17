package main

import (
	"bufio"
	"bytes"
	"context"
	"encoding/base64"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"
)

type testCase struct {
	Args []string `json:"args"`
	Out  string   `json:"out"`
}

type reward struct {
	Reward    float64 `json:"reward"`
	Build     float64 `json:"build"`
	NoPython  float64 `json:"no_python"`
	Behaviour float64 `json:"behaviour"`
}

var errTimeout = errors.New("timeout")

func envOr(key, fallback string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return fallback
}

func runCombined(name string, args []string, dir string, timeout time.Duration) ([]byte, error) {
	ctx, cancel := context.WithTimeout(context.Background(), timeout)
	defer cancel()

	cmd := exec.CommandContext(ctx, name, args...)
	cmd.Dir = dir
	var output bytes.Buffer
	cmd.Stdout = &output
	cmd.Stderr = &output

	err := cmd.Run()
	if ctx.Err() == context.DeadlineExceeded {
		return output.Bytes(), errTimeout
	}
	return output.Bytes(), err
}

func runBinary(binary string, args []string, dir string, timeout time.Duration) ([]byte, string, error) {
	ctx, cancel := context.WithTimeout(context.Background(), timeout)
	defer cancel()

	cmd := exec.CommandContext(ctx, binary, args...)
	cmd.Dir = dir
	var stdout, stderr bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Stderr = &stderr

	err := cmd.Run()
	if ctx.Err() == context.DeadlineExceeded {
		return stdout.Bytes(), stderr.String(), errTimeout
	}
	return stdout.Bytes(), stderr.String(), err
}

func loadCases(path string) ([]testCase, error) {
	handle, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer handle.Close()

	scanner := bufio.NewScanner(handle)
	scanner.Buffer(make([]byte, 64*1024), 16*1024*1024)

	var cases []testCase
	lineNumber := 0
	for scanner.Scan() {
		lineNumber++
		line := strings.TrimSpace(scanner.Text())
		if line == "" {
			continue
		}
		var item testCase
		if err := json.Unmarshal([]byte(line), &item); err != nil {
			return nil, fmt.Errorf("line %d: %w", lineNumber, err)
		}
		cases = append(cases, item)
	}
	if err := scanner.Err(); err != nil {
		return nil, err
	}
	return cases, nil
}

func findPythonFiles(root string) ([]string, error) {
	var files []string
	err := filepath.Walk(root, func(path string, info os.FileInfo, walkErr error) error {
		if walkErr != nil {
			return walkErr
		}
		if !info.IsDir() && strings.EqualFold(filepath.Ext(path), ".py") {
			if len(files) < 20 {
				files = append(files, path)
			}
		}
		return nil
	})
	return files, err
}

func truncate(value string, limit int) string {
	if len(value) <= limit {
		return value
	}
	return value[:limit] + "..."
}

func runBehaviour(binary string, cases []testCase, workDir string) (int, float64) {
	if len(cases) == 0 {
		return 0, 0
	}

	matches := 0
	shown := 0
	deadline := time.Now().Add(8 * time.Minute)

	for index, item := range cases {
		if time.Now().After(deadline) {
			fmt.Printf("global behaviour deadline reached at case %d; remaining cases count as mismatches\n", index)
			break
		}

		stdout, stderr, err := runBinary(binary, item.Args, workDir, 5*time.Second)
		if !errors.Is(err, errTimeout) && bytes.Equal(stdout, []byte(item.Out)) {
			matches++
			continue
		}

		if shown < 10 {
			shown++
			fmt.Printf("MISMATCH case %d args=%q err=%v\n", index, item.Args, err)
			fmt.Printf("  expected=%q\n", truncate(item.Out, 200))
			fmt.Printf("  actual=%q\n", truncate(string(stdout), 200))
			fmt.Printf("  stderr=%q\n", truncate(stderr, 200))
		}
	}

	return matches, float64(matches) / float64(len(cases))
}

func printSecret(binary, secretPath, workDir string) {
	raw, err := os.ReadFile(secretPath)
	if err != nil {
		fmt.Printf("secret read failed: %v\n", err)
		fmt.Println("No secret for you. Yet.")
		return
	}

	decoded, err := base64.StdEncoding.DecodeString(strings.TrimSpace(string(raw)))
	if err != nil {
		fmt.Printf("secret base64 decode failed: %v\n", err)
		fmt.Println("No secret for you. Yet.")
		return
	}

	stdout, stderr, err := runBinary(binary, []string{"-f", "slant", string(decoded)}, workDir, 10*time.Second)
	if err != nil {
		fmt.Printf("secret render failed: %v\n  stderr=%q\n", err, truncate(stderr, 300))
		fmt.Println("No secret for you. Yet.")
		return
	}

	fmt.Println("*** SECRET UNLOCKED ***")
	fmt.Print(string(stdout))
	if len(stdout) == 0 || stdout[len(stdout)-1] != '\n' {
		fmt.Println()
	}
}

func main() {
	repoDir := envOr("HARBOR_REPO_DIR", "/workspace/repo")
	testsDir := envOr("HARBOR_TESTS_DIR", "/tests")
	logsDir := envOr("HARBOR_LOGS_DIR", "/logs/verifier")
	hiddenPath := filepath.Join(testsDir, "data", "hidden.jsonl")
	secretPath := filepath.Join(testsDir, "secret.b64")
	workDir := os.TempDir()
	binaryPath := filepath.Join(workDir, "figlet")

	fmt.Printf("repo=%s\n", repoDir)
	fmt.Printf("hidden=%s\n", hiddenPath)
	fmt.Printf("binary=%s\n", binaryPath)

	buildOutput, buildErr := runCombined("go", []string{"build", "-o", binaryPath, "."}, repoDir, 2*time.Minute)
	buildOK := buildErr == nil
	if buildOK {
		fmt.Println("build OK")
	} else {
		fmt.Printf("build FAILED: %v\n%s\n", buildErr, truncate(string(buildOutput), 4000))
	}

	cases, err := loadCases(hiddenPath)
	if err != nil {
		fmt.Fprintf(os.Stderr, "cannot load hidden cases: %v\n", err)
		os.Exit(1)
	}
	fmt.Printf("hidden cases: %d\n", len(cases))

	matches := 0
	behaviourScore := 0.0
	if buildOK && len(cases) > 0 {
		var behaviour float64
		matches, behaviour = runBehaviour(binaryPath, cases, workDir)
		behaviourScore = behaviour
		fmt.Printf("behaviour: %d/%d matches\n", matches, len(cases))
	} else if !buildOK {
		fmt.Println("build failed; skipping behaviour cases")
	}

	pythonFiles, pythonErr := findPythonFiles(repoDir)
	noPython := false
	if pythonErr != nil {
		fmt.Printf("python scan FAILED: %v\n", pythonErr)
	} else if len(pythonFiles) > 0 {
		fmt.Printf("python files found (%d): %s\n", len(pythonFiles), strings.Join(pythonFiles, ", "))
	} else {
		fmt.Println("no python files found")
		noPython = true
	}

	buildScore := 0.0
	if buildOK {
		buildScore = 1.0
	}
	noPythonScore := 0.0
	if buildOK && noPython && matches > 0 {
		noPythonScore = 1.0
	}

	rewardScore := (buildScore + noPythonScore + 4.0*behaviourScore) / 6.0
	fmt.Printf("build=%.0f no_python=%.0f behaviour=%.6f reward=%.6f\n",
		buildScore, noPythonScore, behaviourScore, rewardScore)

	if buildOK && len(cases) > 0 && matches == len(cases) {
		printSecret(binaryPath, secretPath, workDir)
	} else {
		fmt.Println("No secret for you. Yet.")
	}

	result := reward{
		Reward:    rewardScore,
		Build:     buildScore,
		NoPython:  noPythonScore,
		Behaviour: behaviourScore,
	}
	data, err := json.MarshalIndent(result, "", "  ")
	if err != nil {
		fmt.Fprintf(os.Stderr, "cannot marshal reward: %v\n", err)
		os.Exit(1)
	}
	data = append(data, '\n')

	if err := os.MkdirAll(logsDir, 0o755); err != nil {
		fmt.Fprintf(os.Stderr, "cannot create %s: %v\n", logsDir, err)
		os.Exit(1)
	}
	rewardPath := filepath.Join(logsDir, "reward.json")
	if err := os.WriteFile(rewardPath, data, 0o644); err != nil {
		fmt.Fprintf(os.Stderr, "cannot write %s: %v\n", rewardPath, err)
		os.Exit(1)
	}
	fmt.Printf("wrote %s\n", rewardPath)
}
