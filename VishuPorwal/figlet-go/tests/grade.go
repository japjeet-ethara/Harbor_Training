package main

import (
	"bufio"
	"bytes"
	"context"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"
)

type TestCase struct {
	Args []string `json:"args"`
	Out  string   `json:"out"`
}

type RewardOutput struct {
	Reward    float64 `json:"reward"`
	Build     float64 `json:"build"`
	NoPython  float64 `json:"no_python"`
	Behaviour float64 `json:"behaviour"`
}

func loadHiddenCases(path string) ([]TestCase, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, fmt.Errorf("unable to open dataset file %q: %w", path, err)
	}
	defer f.Close()

	reader := bufio.NewReader(f)
	var cases []TestCase
	lineNum := 0

	for {
		lineBytes, err := reader.ReadBytes('\n')
		if len(lineBytes) == 0 && err == io.EOF {
			break
		}

		lineNum++
		trimmed := bytes.TrimRight(lineBytes, "\r\n")
		if len(trimmed) == 0 {
			return nil, fmt.Errorf("line %d: unexpected empty line in dataset", lineNum)
		}

		var raw map[string]json.RawMessage
		if unmarshalErr := json.Unmarshal(trimmed, &raw); unmarshalErr != nil {
			return nil, fmt.Errorf("line %d: invalid JSON: %w", lineNum, unmarshalErr)
		}

		if len(raw) != 2 {
			return nil, fmt.Errorf("line %d: record must contain exactly 'args' and 'out' keys, found %d keys", lineNum, len(raw))
		}

		rawArgs, hasArgs := raw["args"]
		rawOut, hasOut := raw["out"]
		if !hasArgs || !hasOut {
			return nil, fmt.Errorf("line %d: missing required 'args' or 'out' key", lineNum)
		}

		if bytes.Equal(bytes.TrimSpace(rawArgs), []byte("null")) {
			return nil, fmt.Errorf("line %d: 'args' cannot be null", lineNum)
		}

		var argPtrs []*string
		if unmarshalErr := json.Unmarshal(rawArgs, &argPtrs); unmarshalErr != nil {
			return nil, fmt.Errorf("line %d: 'args' must be a JSON array of strings: %w", lineNum, unmarshalErr)
		}
		if argPtrs == nil {
			return nil, fmt.Errorf("line %d: 'args' cannot be null", lineNum)
		}

		parsedArgs := make([]string, len(argPtrs))
		for idx, ptr := range argPtrs {
			if ptr == nil {
				return nil, fmt.Errorf("line %d: 'args' contains null element at index %d", lineNum, idx)
			}
			parsedArgs[idx] = *ptr
		}

		if bytes.Equal(bytes.TrimSpace(rawOut), []byte("null")) {
			return nil, fmt.Errorf("line %d: 'out' cannot be null", lineNum)
		}

		var outPtr *string
		if unmarshalErr := json.Unmarshal(rawOut, &outPtr); unmarshalErr != nil {
			return nil, fmt.Errorf("line %d: 'out' must be a JSON string: %w", lineNum, unmarshalErr)
		}
		if outPtr == nil {
			return nil, fmt.Errorf("line %d: 'out' cannot be null", lineNum)
		}

		cases = append(cases, TestCase{
			Args: parsedArgs,
			Out:  *outPtr,
		})

		if err != nil {
			if err == io.EOF {
				break
			}
			return nil, fmt.Errorf("line %d: error reading line: %w", lineNum, err)
		}
	}

	if len(cases) != 2000 {
		return nil, fmt.Errorf("invalid record count: expected exactly 2000 records, got %d", len(cases))
	}

	return cases, nil
}

func runBuild(repoDir, binPath string) float64 {
	// Remove stale binary before building
	if err := os.Remove(binPath); err != nil && !os.IsNotExist(err) {
		fmt.Printf("Error: could not remove existing binary %q: %v\n", binPath, err)
		return 0.0
	}

	// 1. go build -o /tmp/figlet .
	fmt.Printf("Building CLI executable in %s...\n", repoDir)
	ctx1, cancel1 := context.WithTimeout(context.Background(), 120*time.Second)
	defer cancel1()

	cmd1 := exec.CommandContext(ctx1, "go", "build", "-o", binPath, ".")
	cmd1.Dir = repoDir
	var out1 bytes.Buffer
	cmd1.Stdout = &out1
	cmd1.Stderr = &out1

	if err := cmd1.Run(); err != nil {
		fmt.Printf("Build step 1 failed ('go build -o %s .'): %v\n", binPath, err)
		if out1.Len() > 0 {
			fmt.Printf("Output:\n%s\n", out1.String())
		}
		return 0.0
	}

	// Verify that the binary was actually created and is not a directory
	if fi, err := os.Stat(binPath); err != nil || fi.IsDir() {
		fmt.Printf("Build step 1 failed: binary %q does not exist or is a directory\n", binPath)
		return 0.0
	}

	// 2. go build ./...
	fmt.Printf("Checking package build ('go build ./...') in %s...\n", repoDir)
	ctx2, cancel2 := context.WithTimeout(context.Background(), 120*time.Second)
	defer cancel2()

	cmd2 := exec.CommandContext(ctx2, "go", "build", "./...")
	cmd2.Dir = repoDir
	var out2 bytes.Buffer
	cmd2.Stdout = &out2
	cmd2.Stderr = &out2

	if err := cmd2.Run(); err != nil {
		fmt.Printf("Build step 2 failed ('go build ./...'): %v\n", err)
		if out2.Len() > 0 {
			fmt.Printf("Output:\n%s\n", out2.String())
		}
		return 0.0
	}

	fmt.Println("Build succeeded: both 'go build -o ... .' and 'go build ./...' passed.")
	return 1.0
}

func runBehaviour(binPath string, cases []TestCase) (float64, int) {
	if len(cases) == 0 {
		return 0.0, 0
	}

	matchingCases := 0
	maxMismatchDiagnostics := 5
	mismatches := 0

	fmt.Printf("Evaluating %d test cases against %s...\n", len(cases), binPath)

	for i, tc := range cases {
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		cmd := exec.CommandContext(ctx, binPath, tc.Args...)
		cmd.Dir = "/tmp"

		var stdout bytes.Buffer
		var stderr bytes.Buffer
		cmd.Stdout = &stdout
		cmd.Stderr = &stderr

		err := cmd.Run()
		timedOut := (ctx.Err() == context.DeadlineExceeded)
		cancel()

		isMatch := (err == nil) && !timedOut && bytes.Equal(stdout.Bytes(), []byte(tc.Out))
		if isMatch {
			matchingCases++
		} else {
			if mismatches < maxMismatchDiagnostics {
				mismatches++
				if timedOut {
					fmt.Printf("[Mismatch %d] Case %d timed out (5s limit). Args: %v\n", mismatches, i+1, tc.Args)
				} else if err != nil {
					errMsg := err.Error()
					if stderr.Len() > 0 {
						errMsg += fmt.Sprintf(" (stderr: %s)", strings.TrimSpace(stderr.String()))
					}
					fmt.Printf("[Mismatch %d] Case %d exited with error: %s. Args: %v\n", mismatches, i+1, errMsg, tc.Args)
				} else {
					fmt.Printf("[Mismatch %d] Case %d stdout mismatch. Expected %d bytes, got %d bytes. Args: %v\n",
						mismatches, i+1, len(tc.Out), stdout.Len(), tc.Args)
				}
			}
		}
	}

	behaviourScore := float64(matchingCases) / float64(len(cases))
	return behaviourScore, matchingCases
}

func checkNoPython(repoDir string, buildPassed bool, matchingCases int) float64 {
	if !buildPassed || matchingCases < 1 {
		return 0.0
	}

	hasPython := false
	var sampleFiles []string

	err := filepath.Walk(repoDir, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}
		if !info.IsDir() && strings.HasSuffix(strings.ToLower(info.Name()), ".py") {
			hasPython = true
			if len(sampleFiles) < 5 {
				sampleFiles = append(sampleFiles, path)
			}
		}
		return nil
	})

	if err != nil {
		fmt.Fprintf(os.Stderr, "Error traversing %q for Python files: %v\n", repoDir, err)
		return 0.0
	}

	if hasPython {
		fmt.Printf("Python source files still present under %q (e.g. %v)\n", repoDir, sampleFiles)
		return 0.0
	}

	fmt.Printf("No Python source files found under %q.\n", repoDir)
	return 1.0
}

func writeReward(rewardPath string, out RewardOutput) error {
	dir := filepath.Dir(rewardPath)
	if err := os.MkdirAll(dir, 0755); err != nil {
		return fmt.Errorf("failed to create verifier log directory %q: %w", dir, err)
	}

	data, err := json.MarshalIndent(out, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to encode reward JSON: %w", err)
	}
	data = append(data, '\n')

	if err := os.WriteFile(rewardPath, data, 0644); err != nil {
		return fmt.Errorf("failed to write reward file %q: %w", rewardPath, err)
	}

	return nil
}

func handleSecret(binPath, secretPath string, matchingCases, totalCases int) {
	if matchingCases < totalCases || totalCases == 0 {
		fmt.Println("No secret for you. Yet.")
		return
	}

	data, err := os.ReadFile(secretPath)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Secret error: unable to read %q: %v\n", secretPath, err)
		return
	}

	trimmed := strings.TrimSpace(string(data))
	decodedBytes, err := base64.StdEncoding.DecodeString(trimmed)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Secret error: base64 decode failed for %q: %v\n", secretPath, err)
		return
	}

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	cmd := exec.CommandContext(ctx, binPath, "-f", "slant", string(decodedBytes))
	cmd.Dir = "/tmp"

	var stdout bytes.Buffer
	var stderr bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Stderr = &stderr

	if err := cmd.Run(); err != nil {
		fmt.Fprintf(os.Stderr, "Secret error: failed to render banner: %v (stderr: %s)\n", err, strings.TrimSpace(stderr.String()))
		return
	}

	outStr := stdout.String()
	fmt.Println("*** SECRET UNLOCKED ***")
	if strings.HasSuffix(outStr, "\n") {
		fmt.Print(outStr)
	} else {
		fmt.Println(outStr)
	}
}

func main() {
	const (
		datasetPath = "/tests/data/hidden.jsonl"
		repoDir     = "/workspace/repo"
		binPath     = "/tmp/figlet"
		secretPath  = "/tests/secret.b64"
		rewardPath  = "/logs/verifier/reward.json"
	)

	// 1. Load dataset (infrastructure check)
	cases, err := loadHiddenCases(datasetPath)
	if err != nil {
		fmt.Fprintf(os.Stderr, "VERIFIER INFRASTRUCTURE ERROR: %v\n", err)
		os.Exit(1)
	}

	// 2. Build
	buildScore := runBuild(repoDir, binPath)
	buildPassed := (buildScore == 1.0)

	// 3. Behaviour
	var behaviourScore float64
	var matchingCases int
	if buildPassed {
		behaviourScore, matchingCases = runBehaviour(binPath, cases)
	} else {
		fmt.Println("Build failed; skipping behavioral test cases.")
		behaviourScore = 0.0
		matchingCases = 0
	}

	// 4. No Python check
	noPythonScore := checkNoPython(repoDir, buildPassed, matchingCases)

	// 5. Reward calculation and writing
	reward := (buildScore + noPythonScore + 4.0*behaviourScore) / 6.0

	rewardOutput := RewardOutput{
		Reward:    reward,
		Build:     buildScore,
		NoPython:  noPythonScore,
		Behaviour: behaviourScore,
	}

	if err := writeReward(rewardPath, rewardOutput); err != nil {
		fmt.Fprintf(os.Stderr, "Error writing reward file: %v\n", err)
		os.Exit(1)
	}

	// Summary output
	fmt.Println("\n=== FIGLET-GO GRADING SUMMARY ===")
	fmt.Printf("Build:          %.6f\n", buildScore)
	fmt.Printf("Behaviour:      %.6f (%d/%d cases matched)\n", behaviourScore, matchingCases, len(cases))
	fmt.Printf("No Python:      %.6f\n", noPythonScore)
	fmt.Printf("Total Reward:   %.6f\n", reward)
	fmt.Println("=================================")

	// 6. Secret mechanism
	handleSecret(binPath, secretPath, matchingCases, len(cases))
}
