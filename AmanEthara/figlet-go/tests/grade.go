package main

import (
	"bufio"
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

type RewardData struct {
	Reward    float64 `json:"reward"`
	Build     float64 `json:"build"`
	NoPython  float64 `json:"no_python"`
	Behaviour float64 `json:"behaviour"`
}

func writeReward(data RewardData) error {
	if err := os.MkdirAll("/logs/verifier", 0755); err != nil {
		return err
	}
	bytes, err := json.MarshalIndent(data, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile("/logs/verifier/reward.json", bytes, 0644)
}

func main() {
	var buildScore float64
	var noPythonScore float64
	var behaviourScore float64

	repoDir := "/workspace/repo"
	binaryPath := "/tmp/figlet"

	fmt.Println("=== Starting FIGlet Go Grading ===")

	// 1. Build check (weight 1)
	buildCmd := exec.Command("go", "build", "-o", binaryPath, ".")
	buildCmd.Dir = repoDir
	buildOutput, err := buildCmd.CombinedOutput()
	if err != nil {
		fmt.Printf("Build FAILED: %v\n%s\n", err, string(buildOutput))
		buildScore = 0.0
		noPythonScore = 0.0
		behaviourScore = 0.0
		totalReward := 0.0
		_ = writeReward(RewardData{
			Reward:    totalReward,
			Build:     buildScore,
			NoPython:  noPythonScore,
			Behaviour: behaviourScore,
		})
		fmt.Println("No secret for you. Yet.")
		return
	}

	buildScore = 1.0
	fmt.Println("Build PASSED (weight 1/6)")

	// Check for Python files in /workspace/repo
	hasPython := false
	_ = filepath.Walk(repoDir, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return nil
		}
		if !info.IsDir() && strings.HasSuffix(strings.ToLower(info.Name()), ".py") {
			hasPython = true
			fmt.Printf("Found Python file: %s\n", path)
		}
		return nil
	})

	// 2. Hidden behavior check (weight 4)
	hiddenDataPath := "/tests/data/hidden.jsonl"
	file, err := os.Open(hiddenDataPath)
	if err != nil {
		fmt.Printf("Error opening hidden test data %s: %v\n", hiddenDataPath, err)
		_ = writeReward(RewardData{
			Reward:    (buildScore * 1.0) / 6.0,
			Build:     buildScore,
			NoPython:  0.0,
			Behaviour: 0.0,
		})
		fmt.Println("No secret for you. Yet.")
		return
	}
	defer file.Close()

	scanner := bufio.NewScanner(file)
	buf := make([]byte, 1024*1024)
	scanner.Buffer(buf, 10*1024*1024)

	var totalCases int
	var matchedCases int
	var failures []string

	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if line == "" {
			continue
		}
		totalCases++

		var tc TestCase
		if err := json.Unmarshal([]byte(line), &tc); err != nil {
			if len(failures) < 10 {
				failures = append(failures, fmt.Sprintf("Case %d: invalid JSON: %v", totalCases, err))
			}
			continue
		}

		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		cmd := exec.CommandContext(ctx, binaryPath, tc.Args...)
		cmd.Dir = "/tmp"
		out, err := cmd.Output()
		cancel()

		if err == nil && string(out) == tc.Out {
			matchedCases++
		} else if len(failures) < 10 {
			if ctx.Err() == context.DeadlineExceeded {
				failures = append(failures, fmt.Sprintf("Case %d: timed out", totalCases))
			} else if err != nil {
				failures = append(failures, fmt.Sprintf("Case %d: exit error: %v", totalCases, err))
			} else {
				failures = append(failures, fmt.Sprintf("Case %d: output mismatch (expected %d bytes, got %d bytes)", totalCases, len(tc.Out), len(out)))
			}
		}
	}

	if totalCases > 0 {
		behaviourScore = float64(matchedCases) / float64(totalCases)
	}
	fmt.Printf("Behavior: %d/%d passed (score: %.4f, weight 4/6)\n", matchedCases, totalCases, behaviourScore)
	for _, fail := range failures {
		fmt.Println("  ", fail)
	}

	// 3. No-Python check (weight 1)
	// no_python (weight 1): 1 only if build passed AND no .py file exists under /workspace/repo AND at least one hidden case below matches; else 0.
	if buildScore == 1.0 && !hasPython && matchedCases > 0 {
		noPythonScore = 1.0
		fmt.Println("No-Python PASSED (weight 1/6)")
	} else {
		noPythonScore = 0.0
		fmt.Printf("No-Python FAILED (build=%.0f, hasPython=%v, matched=%d)\n", buildScore, hasPython, matchedCases)
	}

	// Calculate weighted reward
	totalReward := (buildScore*1.0 + noPythonScore*1.0 + behaviourScore*4.0) / 6.0
	fmt.Printf("Final Reward: %.6f\n", totalReward)

	rewardObj := RewardData{
		Reward:    totalReward,
		Build:     buildScore,
		NoPython:  noPythonScore,
		Behaviour: behaviourScore,
	}

	if err := writeReward(rewardObj); err != nil {
		fmt.Printf("Error writing reward.json: %v\n", err)
	}

	// 4. Secret unlock
	if behaviourScore == 1.0 {
		secretBytes, err := os.ReadFile("/tests/secret.b64")
		if err != nil {
			fmt.Printf("Error reading secret file: %v\n", err)
		} else {
			decoded, err := base64.StdEncoding.DecodeString(strings.TrimSpace(string(secretBytes)))
			if err != nil {
				fmt.Printf("Error decoding secret: %v\n", err)
			} else {
				secretCmd := exec.Command(binaryPath, "-f", "slant", string(decoded))
				secretCmd.Dir = "/tmp"
				secretOut, err := secretCmd.CombinedOutput()
				if err != nil {
					fmt.Printf("Error rendering secret: %v\n%s\n", err, string(secretOut))
				} else {
					fmt.Println("*** SECRET UNLOCKED ***")
					fmt.Print(string(secretOut))
				}
			}
		}
	} else {
		fmt.Println("No secret for you. Yet.")
	}
}
