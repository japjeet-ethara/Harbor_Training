package main

import (
	"bufio"
	"bytes"
	"context"
	"encoding/base64"
	"encoding/json"
	"fmt"
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

func loadTestCases(path string) ([]TestCase, error) {
	file, err := os.Open(path)
	if err != nil {
		return nil, fmt.Errorf("failed to open test cases file %s: %w", path, err)
	}
	defer file.Close()

	var testCases []TestCase
	scanner := bufio.NewScanner(file)
	const maxLineLen = 10 * 1024 * 1024
	buf := make([]byte, 64*1024)
	scanner.Buffer(buf, maxLineLen)

	lineNum := 0
	for scanner.Scan() {
		lineNum++
		line := strings.TrimSpace(scanner.Text())
		if line == "" {
			continue
		}
		var tc TestCase
		if err := json.Unmarshal([]byte(line), &tc); err != nil {
			return nil, fmt.Errorf("failed to parse JSON in %s at line %d: %w", path, lineNum, err)
		}
		testCases = append(testCases, tc)
	}

	if err := scanner.Err(); err != nil {
		return nil, fmt.Errorf("scanner error while reading %s: %w", path, err)
	}

	return testCases, nil
}

func checkBuild() (float64, error) {
	repoDir := "/workspace/repo"
	if _, err := os.Stat(repoDir); os.IsNotExist(err) {
		if _, errLocal := os.Stat("repo"); errLocal == nil {
			repoDir = "repo"
		} else if _, errLocal2 := os.Stat("../repo"); errLocal2 == nil {
			repoDir = "../repo"
		}
	}
	cmd := exec.Command("go", "build", "-o", "/tmp/figlet", ".")
	cmd.Dir = repoDir
	var outBuf, errBuf bytes.Buffer
	cmd.Stdout = &outBuf
	cmd.Stderr = &errBuf

	err := cmd.Run()
	if err != nil {
		fmt.Printf("Build check failed: %v\nStderr: %s\n", err, errBuf.String())
		return 0.0, err
	}
	fmt.Println("Build check passed: /tmp/figlet built successfully.")
	return 1.0, nil
}

func checkNoPython() bool {
	repoDir := "/workspace/repo"
	if _, err := os.Stat(repoDir); os.IsNotExist(err) {
		if _, errLocal := os.Stat("repo"); errLocal == nil {
			repoDir = "repo"
		} else if _, errLocal2 := os.Stat("../repo"); errLocal2 == nil {
			repoDir = "../repo"
		}
	}
	hasPython := false
	err := filepath.Walk(repoDir, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return nil
		}
		if !info.IsDir() && strings.HasSuffix(strings.ToLower(info.Name()), ".py") {
			hasPython = true
			fmt.Printf("Found python file in repository: %s\n", path)
		}
		return nil
	})
	if err != nil {
		fmt.Printf("Warning: error walking %s: %v\n", repoDir, err)
	}
	return !hasPython
}

func getFigletBinary() string {
	bin := "/tmp/figlet"
	if _, err := os.Stat(bin); os.IsNotExist(err) {
		if _, errExe := os.Stat(bin + ".exe"); errExe == nil {
			return bin + ".exe"
		}
	}
	return bin
}

func runCase(ctx context.Context, figletBin string, tc TestCase) bool {
	ctxCase, cancel := context.WithTimeout(ctx, 5*time.Second)
	defer cancel()

	cmd := exec.CommandContext(ctxCase, figletBin, tc.Args...)
	var stdoutBuf bytes.Buffer
	cmd.Stdout = &stdoutBuf

	err := cmd.Run()
	if err != nil {
		return false
	}
	return stdoutBuf.String() == tc.Out
}

func main() {
	fmt.Println("=== Starting Harbor Figlet Grader ===")

	// 1. Check build (weight 1)
	buildScore, _ := checkBuild()
	figletBin := getFigletBinary()

	// Locate hidden.jsonl
	hiddenPath := "/tests/data/hidden.jsonl"
	if _, err := os.Stat(hiddenPath); os.IsNotExist(err) {
		if _, errRel := os.Stat("data/hidden.jsonl"); errRel == nil {
			hiddenPath = "data/hidden.jsonl"
		} else if _, errTest := os.Stat("tests/data/hidden.jsonl"); errTest == nil {
			hiddenPath = "tests/data/hidden.jsonl"
		}
	}

	testCases, err := loadTestCases(hiddenPath)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error loading test cases: %v\n", err)
		os.Exit(1)
	}

	totalCases := len(testCases)
	matchedCases := 0

	// 3. Evaluate behaviour (weight 4) if build passed
	if buildScore == 1.0 && totalCases > 0 {
		fmt.Printf("Evaluating %d hidden cases (5s timeout each)...\n", totalCases)
		for i, tc := range testCases {
			if runCase(context.Background(), figletBin, tc) {
				matchedCases++
			}
			if (i+1)%500 == 0 || i+1 == totalCases {
				fmt.Printf("Progress: %d/%d cases evaluated (matched: %d)\n", i+1, totalCases, matchedCases)
			}
		}
	} else if buildScore == 0.0 {
		fmt.Println("Build failed; skipping behaviour test suite.")
	}

	var behaviourScore float64
	if totalCases > 0 {
		behaviourScore = float64(matchedCases) / float64(totalCases)
	}

	// 2. Check no_python (weight 1):
	// 1 only if build passed AND no .py file exists AND at least one hidden case matched
	var noPythonScore float64
	noPy := checkNoPython()
	if buildScore == 1.0 && noPy && matchedCases >= 1 {
		noPythonScore = 1.0
		fmt.Println("no_python check passed: build succeeded, no .py files present, and at least one case matched.")
	} else {
		noPythonScore = 0.0
		fmt.Printf("no_python check: 0.0 (build=%.1f, no_py_files=%v, matched=%d)\n", buildScore, noPy, matchedCases)
	}

	// 4. Calculate weighted mean reward
	// weights: build (1), no_python (1), behaviour (4) -> total = 6
	reward := (1.0*buildScore + 1.0*noPythonScore + 4.0*behaviourScore) / 6.0

	rewardResult := RewardOutput{
		Reward:    reward,
		Build:     buildScore,
		NoPython:  noPythonScore,
		Behaviour: behaviourScore,
	}

	// Write /logs/verifier/reward.json
	logsDir := "/logs/verifier"
	_ = os.MkdirAll(logsDir, 0755)
	rewardPath := filepath.Join(logsDir, "reward.json")
	rewardData, err := json.MarshalIndent(rewardResult, "", "  ")
	if err == nil {
		_ = os.WriteFile(rewardPath, rewardData, 0644)
		fmt.Printf("Wrote reward to %s:\n%s\n", rewardPath, string(rewardData))
	} else {
		fmt.Printf("Error marshalling reward json: %v\n", err)
	}

	// Local fallback copy if /logs/verifier does not exist
	if _, err := os.Stat("/logs/verifier"); os.IsNotExist(err) {
		_ = os.WriteFile("reward.json", rewardData, 0644)
	}

	// 5. SECRET handling
	if behaviourScore == 1.0 && totalCases > 0 {
		fmt.Println("\n*** SECRET UNLOCKED ***")
		secretPath := "/tests/secret.b64"
		if _, err := os.Stat(secretPath); os.IsNotExist(err) {
			if _, errRel := os.Stat("secret.b64"); errRel == nil {
				secretPath = "secret.b64"
			} else if _, errTest := os.Stat("tests/secret.b64"); errTest == nil {
				secretPath = "tests/secret.b64"
			}
		}
		secretBytes, err := os.ReadFile(secretPath)
		if err != nil {
			fmt.Printf("Error reading secret file: %v\n", err)
		} else {
			cleanB64 := strings.TrimSpace(string(secretBytes))
			decoded, err := base64.StdEncoding.DecodeString(cleanB64)
			if err != nil {
				fmt.Printf("Error decoding base64 secret: %v\n", err)
			} else {
				cmd := exec.Command(figletBin, "-f", "slant", strings.TrimRight(string(decoded), "\r\n"))
				cmd.Stdout = os.Stdout
				cmd.Stderr = os.Stderr
				_ = cmd.Run()
			}
		}
	} else {
		fmt.Println("\nNo secret for you. Yet.")
	}
}
