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

type RewardOutput struct {
	Reward    float64 `json:"reward"`
	Build     float64 `json:"build"`
	NoPython  float64 `json:"no_python"`
	Behaviour float64 `json:"behaviour"`
}

type TestCase struct {
	Args []string `json:"args"`
	Out  string   `json:"out"`
}

func writeReward(r RewardOutput) {
	_ = os.MkdirAll("/logs/verifier", 0777)
	data, _ := json.Marshal(r)
	_ = os.WriteFile("/logs/verifier/reward.json", data, 0666)
	fmt.Println(string(data))
}

func main() {
	// 1. COMPONENT: build (weight 1)
	buildCmd := exec.Command("go", "build", "-o", "/tmp/figlet", ".")
	buildCmd.Dir = "/workspace/repo"
	if _, err := buildCmd.CombinedOutput(); err != nil {
		writeReward(RewardOutput{
			Reward:    0.0,
			Build:     0.0,
			NoPython:  0.0,
			Behaviour: 0.0,
		})
		fmt.Println("No secret for you. Yet.")
		os.Exit(0)
	}
	build := 1.0

	// 2. Check for .py files under /workspace/repo
	hasPy := false
	_ = filepath.Walk("/workspace/repo", func(path string, info os.FileInfo, err error) error {
		if err == nil && !info.IsDir() && strings.HasSuffix(strings.ToLower(info.Name()), ".py") {
			hasPy = true
		}
		return nil
	})

	// 3. COMPONENT: behaviour (weight 4)
	totalCases := 0
	matchedCases := 0

	dataFile, err := os.Open("/tests/data/hidden.jsonl")
	if err != nil {
		fmt.Printf("Error opening hidden test cases: %v\n", err)
	} else {
		defer dataFile.Close()
		scanner := bufio.NewScanner(dataFile)
		// Allow scanning larger lines if necessary
		buf := make([]byte, 1024*1024)
		scanner.Buffer(buf, 10*1024*1024)

		for scanner.Scan() {
			line := scanner.Bytes()
			if len(bytes.TrimSpace(line)) == 0 {
				continue
			}
			var tc TestCase
			if err := json.Unmarshal(line, &tc); err != nil {
				continue
			}
			totalCases++

			ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
			cmd := exec.CommandContext(ctx, "/tmp/figlet", tc.Args...)
			cmd.Dir = "/workspace/repo"

			var stdout bytes.Buffer
			cmd.Stdout = &stdout

			if err := cmd.Run(); err == nil {
				if bytes.Equal(stdout.Bytes(), []byte(tc.Out)) {
					matchedCases++
				}
			}
			cancel()
		}
	}

	behaviour := 0.0
	if totalCases > 0 {
		behaviour = float64(matchedCases) / float64(totalCases)
	}

	// 2. COMPONENT: no_python (weight 1)
	noPython := 0.0
	if build == 1.0 && !hasPy && matchedCases >= 1 {
		noPython = 1.0
	}

	// 4. REWARD CALCULATION
	reward := (build*1.0 + noPython*1.0 + behaviour*4.0) / 6.0
	writeReward(RewardOutput{
		Reward:    reward,
		Build:     build,
		NoPython:  noPython,
		Behaviour: behaviour,
	})

	// 5. SECRET
	if behaviour == 1.0 {
		secretRaw, err := os.ReadFile("/tests/secret.b64")
		if err != nil {
			fmt.Printf("Error reading secret: %v\n", err)
			return
		}
		decoded, err := base64.StdEncoding.DecodeString(strings.TrimSpace(string(secretRaw)))
		if err != nil {
			fmt.Printf("Error decoding secret: %v\n", err)
			return
		}
		secretText := string(decoded)

		secretCmd := exec.Command("/tmp/figlet", "-f", "slant", secretText)
		secretCmd.Dir = "/workspace/repo"
		out, err := secretCmd.CombinedOutput()
		if err != nil {
			fmt.Printf("Error running figlet for secret: %v\n", err)
			return
		}

		fmt.Println("*** SECRET UNLOCKED ***")
		fmt.Print(string(out))
	} else {
		fmt.Println("No secret for you. Yet.")
	}
}
