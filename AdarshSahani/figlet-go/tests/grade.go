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

const (
	repoDir    = "/workspace/repo"
	hiddenFile = "/tests/data/hidden.jsonl"
	figletBin  = "/tmp/figlet"
	rewardFile = "/logs/verifier/reward.json"
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

func main() {
	result := grade()
	if err := writeReward(result); err != nil {
		fmt.Fprintf(os.Stderr, "cannot write reward: %v\n", err)
		os.Exit(1)
	}

	if result.Behaviour == 1 {
		unlockSecret()
	} else {
		fmt.Println("No secret for you. Yet.")
	}
}

func grade() reward {
	result := reward{}
	_ = os.Remove(figletBin) // Never allow an old binary to affect this run.

	build := exec.Command("go", "build", "-o", figletBin, ".")
	build.Dir = repoDir
	if err := build.Run(); err == nil {
		result.Build = 1
	}

	cases, err := readCases(hiddenFile)
	if err != nil || len(cases) == 0 {
		writeWeightedReward(&result)
		return result
	}

	if result.Build == 1 {
		matches := 0
		for _, tc := range cases {
			if runCase(tc) {
				matches++
			}
		}
		result.Behaviour = float64(matches) / float64(len(cases))
		if matches > 0 && !containsPython(repoDir) {
			result.NoPython = 1
		}
	}
	writeWeightedReward(&result)
	return result
}

func writeWeightedReward(result *reward) {
	result.Reward = (result.Build + result.NoPython + 4*result.Behaviour) / 6
}

func readCases(path string) ([]testCase, error) {
	file, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer file.Close()

	var cases []testCase
	scanner := bufio.NewScanner(file)
	scanner.Buffer(make([]byte, 64*1024), 64*1024*1024)
	for scanner.Scan() {
		line := bytes.TrimSpace(scanner.Bytes())
		if len(line) == 0 {
			continue
		}
		var tc testCase
		if err := json.Unmarshal(line, &tc); err != nil {
			return nil, fmt.Errorf("decode hidden case %d: %w", len(cases)+1, err)
		}
		cases = append(cases, tc)
	}
	if err := scanner.Err(); err != nil {
		return nil, err
	}
	return cases, nil
}

func runCase(tc testCase) bool {
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	cmd := exec.CommandContext(ctx, figletBin, tc.Args...)
	cmd.Dir = repoDir
	var stdout bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Stderr = io.Discard
	if err := cmd.Run(); err != nil {
		return false
	}
	return bytes.Equal(stdout.Bytes(), []byte(tc.Out))
}

func containsPython(root string) bool {
	found := false
	err := filepath.WalkDir(root, func(path string, entry os.DirEntry, err error) error {
		if err != nil {
			return err
		}
		if entry.IsDir() {
			return nil
		}
		if strings.EqualFold(filepath.Ext(entry.Name()), ".py") {
			found = true
			return filepath.SkipAll
		}
		return nil
	})
	return found || err != nil
}

func writeReward(result reward) error {
	data, err := json.Marshal(result)
	if err != nil {
		return err
	}
	if err := os.MkdirAll(filepath.Dir(rewardFile), 0o755); err != nil {
		return err
	}
	return os.WriteFile(rewardFile, append(data, '\n'), 0o644)
}

func unlockSecret() {
	encoded, err := os.ReadFile("/tests/secret.b64")
	if err != nil {
		fmt.Fprintf(os.Stderr, "cannot read unlock input: %v\n", err)
		return
	}
	decoded, err := base64.StdEncoding.DecodeString(strings.TrimSpace(string(encoded)))
	if err != nil {
		fmt.Fprintf(os.Stderr, "cannot decode unlock input: %v\n", err)
		return
	}

	cmd := exec.Command(figletBin, append([]string{"-f", "slant"}, string(decoded))...)
	cmd.Dir = repoDir
	output, err := cmd.Output()
	if err != nil {
		fmt.Fprintf(os.Stderr, "cannot render unlock input: %v\n", err)
		return
	}
	fmt.Println("*** SECRET UNLOCKED ***")
	_, _ = os.Stdout.Write(output)
}
