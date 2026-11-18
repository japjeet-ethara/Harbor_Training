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

type RewardReport struct {
	Reward    float64 `json:"reward"`
	Build     float64 `json:"build"`
	NoPython  float64 `json:"no_python"`
	Behaviour float64 `json:"behaviour"`
}

type TestCase struct {
	Args []string `json:"args"`
	Out  string   `json:"out"`
}

func main() {
	repoDir := "/workspace/repo"
	binaryPath := "/tmp/figlet"

	hiddenPath := "/tests/data/hidden.jsonl"
	if _, err := os.Stat(hiddenPath); os.IsNotExist(err) {
		hiddenPath = "data/hidden.jsonl"
	}

	secretPath := "/tests/secret.b64"
	if _, err := os.Stat(secretPath); os.IsNotExist(err) {
		secretPath = "secret.b64"
	}

	logsDir := "/logs/verifier"
	rewardJsonPath := filepath.Join(logsDir, "reward.json")
	rewardTxtPath := filepath.Join(logsDir, "reward.txt")

	// 1. Build check (weight 1)
	buildScore := 0.0
	cmdBuild := exec.Command("go", "build", "-o", binaryPath, ".")
	cmdBuild.Dir = repoDir
	if err := cmdBuild.Run(); err == nil {
		if fi, err := os.Stat(binaryPath); err == nil && !fi.IsDir() {
			buildScore = 1.0
		}
	}

	// 3. Behaviour check (weight 4)
	matchedCases := 0
	totalCases := 0

	if buildScore == 1.0 {
		file, err := os.Open(hiddenPath)
		if err == nil {
			scanner := bufio.NewScanner(file)
			// Increase buffer size for large lines
			buf := make([]byte, 1024*1024)
			scanner.Buffer(buf, 10*1024*1024)

			for scanner.Scan() {
				line := scanner.Bytes()
				if len(line) == 0 {
					continue
				}
				totalCases++

				var tc TestCase
				if err := json.Unmarshal(line, &tc); err != nil {
					continue
				}

				ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
				cmdCase := exec.CommandContext(ctx, binaryPath, tc.Args...)
				cmdCase.Dir = "/tmp"

				var stdout bytes.Buffer
				cmdCase.Stdout = &stdout

				err := cmdCase.Run()
				cancel()

				if err == nil && bytes.Equal(stdout.Bytes(), []byte(tc.Out)) {
					matchedCases++
				}
			}
			file.Close()
		}
	}

	behaviourScore := 0.0
	if totalCases > 0 {
		behaviourScore = float64(matchedCases) / float64(totalCases)
	}

	// 2. no_python check (weight 1)
	// 1 only if build passed AND no .py file exists under /workspace/repo AND at least one hidden case matches; else 0
	noPythonScore := 0.0
	if buildScore == 1.0 && matchedCases >= 1 {
		hasPython := false
		_ = filepath.Walk(repoDir, func(path string, info os.FileInfo, err error) error {
			if err != nil {
				return nil
			}
			if !info.IsDir() && strings.HasSuffix(strings.ToLower(info.Name()), ".py") {
				hasPython = true
				return filepath.SkipAll
			}
			return nil
		})
		if !hasPython {
			noPythonScore = 1.0
		}
	}

	// Weighted mean: build (1), no_python (1), behaviour (4) => sum of weights = 6
	weightedReward := (1.0*buildScore + 1.0*noPythonScore + 4.0*behaviourScore) / 6.0

	report := RewardReport{
		Reward:    weightedReward,
		Build:     buildScore,
		NoPython:  noPythonScore,
		Behaviour: behaviourScore,
	}

	// 4. Write /logs/verifier/reward.json
	_ = os.MkdirAll(logsDir, 0755)
	if jsonData, err := json.MarshalIndent(report, "", "  "); err == nil {
		_ = os.WriteFile(rewardJsonPath, jsonData, 0644)
	}
	_ = os.WriteFile(rewardTxtPath, []byte(fmt.Sprintf("%.6f\n", weightedReward)), 0644)

	fmt.Printf("Evaluation Summary:\n")
	fmt.Printf("  Build:     %.2f (weight 1)\n", buildScore)
	fmt.Printf("  No Python: %.2f (weight 1)\n", noPythonScore)
	fmt.Printf("  Behaviour: %.4f (%d/%d cases, weight 4)\n", behaviourScore, matchedCases, totalCases)
	fmt.Printf("  Reward:    %.4f\n\n", weightedReward)

	// 5. SECRET
	if behaviourScore == 1.0 {
		secretData, err := os.ReadFile(secretPath)
		if err == nil {
			trimmedB64 := strings.TrimSpace(string(secretData))
			decodedText, err := base64.StdEncoding.DecodeString(trimmedB64)
			if err == nil {
				cmdSecret := exec.Command(binaryPath, "-f", "slant", string(decodedText))
				cmdSecret.Dir = "/tmp"
				out, err := cmdSecret.CombinedOutput()
				if err == nil {
					fmt.Println("*** SECRET UNLOCKED ***")
					fmt.Print(string(out))
					return
				}
			}
		}
	}

	fmt.Println("No secret for you. Yet.")
}
