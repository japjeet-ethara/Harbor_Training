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

type RewardReport struct {
	Reward    float64 `json:"reward"`
	Build     float64 `json:"build"`
	NoPython  float64 `json:"no_python"`
	Behaviour float64 `json:"behaviour"`
}

func main() {
	var buildScore float64 = 0.0
	var noPythonScore float64 = 0.0
	var behaviourScore float64 = 0.0

	// 1. Build check
	buildCmd := exec.Command("go", "build", "-o", "/tmp/figlet", ".")
	buildCmd.Dir = "/workspace/repo"
	var buildBuf bytes.Buffer
	buildCmd.Stdout = &buildBuf
	buildCmd.Stderr = &buildBuf
	if err := buildCmd.Run(); err == nil {
		buildScore = 1.0
		fmt.Println("Build succeeded.")
	} else {
		fmt.Printf("Build failed: %v\nOutput: %s\n", err, buildBuf.String())
	}

	// 2. Check for .py files in /workspace/repo
	pyFound := false
	_ = filepath.Walk("/workspace/repo", func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return nil
		}
		if !info.IsDir() && strings.HasSuffix(strings.ToLower(info.Name()), ".py") {
			pyFound = true
		}
		return nil
	})

	// 3. Behaviour check using /tests/data/hidden.jsonl
	hiddenPath := "/tests/data/hidden.jsonl"
	if _, err := os.Stat(hiddenPath); os.IsNotExist(err) {
		hiddenPath = "data/hidden.jsonl"
	}

	totalCases := 0
	matchedCases := 0

	if buildScore == 1.0 {
		file, err := os.Open(hiddenPath)
		if err != nil {
			fmt.Printf("Could not open %s: %v\n", hiddenPath, err)
		} else {
			defer file.Close()
			scanner := bufio.NewScanner(file)
			// Allow large lines
			buf := make([]byte, 1024*1024)
			scanner.Buffer(buf, 10*1024*1024)

			for scanner.Scan() {
				line := scanner.Text()
				if strings.TrimSpace(line) == "" {
					continue
				}
				var tc TestCase
				if err := json.Unmarshal([]byte(line), &tc); err != nil {
					continue
				}
				totalCases++

				ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
				cmd := exec.CommandContext(ctx, "/tmp/figlet", tc.Args...)
				var outBuf bytes.Buffer
				cmd.Stdout = &outBuf
				_ = cmd.Run()
				cancel()

				if outBuf.String() == tc.Out {
					matchedCases++
				}
			}
			if err := scanner.Err(); err != nil {
				fmt.Printf("Error scanning %s: %v\n", hiddenPath, err)
			}
		}
	}

	if totalCases > 0 {
		behaviourScore = float64(matchedCases) / float64(totalCases)
	}

	// Rule 2: no_python = 1 only if build passed AND no .py file exists AND at least one hidden case matches
	if buildScore == 1.0 && !pyFound && matchedCases > 0 {
		noPythonScore = 1.0
	} else {
		noPythonScore = 0.0
	}

	// 4. Calculate weighted mean reward: (1*build + 1*no_python + 4*behaviour) / 6.0
	reward := (1.0*buildScore + 1.0*noPythonScore + 4.0*behaviourScore) / 6.0

	fmt.Printf("Scores -> Build: %.4f, NoPython: %.4f, Behaviour: %.4f (%d/%d), Reward: %.4f\n",
		buildScore, noPythonScore, behaviourScore, matchedCases, totalCases, reward)

	// Write /logs/verifier/reward.json
	report := RewardReport{
		Reward:    reward,
		Build:     buildScore,
		NoPython:  noPythonScore,
		Behaviour: behaviourScore,
	}

	_ = os.MkdirAll("/logs/verifier", 0755)
	reportBytes, _ := json.MarshalIndent(report, "", "  ")
	_ = os.WriteFile("/logs/verifier/reward.json", reportBytes, 0644)

	// 5. SECRET logic
	if behaviourScore == 1.0 {
		secretPath := "/tests/secret.b64"
		if _, err := os.Stat(secretPath); os.IsNotExist(err) {
			secretPath = "secret.b64"
		}
		secretB64, err := os.ReadFile(secretPath)
		if err == nil {
			decoded, err := base64.StdEncoding.DecodeString(strings.TrimSpace(string(secretB64)))
			if err == nil {
				secCmd := exec.Command("/tmp/figlet", "-f", "slant", string(decoded))
				secOut, secErr := secCmd.CombinedOutput()
				if secErr == nil {
					fmt.Println("*** SECRET UNLOCKED ***")
					fmt.Print(string(secOut))
				} else {
					fmt.Printf("Error rendering secret: %v\n", secErr)
				}
			} else {
				fmt.Printf("Error decoding secret: %v\n", err)
			}
		} else {
			fmt.Printf("Error reading secret file: %v\n", err)
		}
	} else {
		fmt.Println("No secret for you. Yet.")
	}
}
