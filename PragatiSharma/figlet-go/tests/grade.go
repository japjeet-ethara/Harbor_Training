package main

import (
	"bufio"
	"bytes"
	"context"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"math"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"
)

// TestCase mirrors one line of hidden.jsonl.
type TestCase struct {
	Args []string `json:"args"`
	Out  string   `json:"out"`
}

// Reward is the grading output written to reward.json.
type Reward struct {
	Reward    float64 `json:"reward"`
	Build     float64 `json:"build"`
	NoPython  float64 `json:"no_python"`
	Behaviour float64 `json:"behaviour"`
}

const (
	repoDir       = "/workspace/repo"
	figletBin     = "/tmp/figlet"
	hiddenFile    = "/tests/data/hidden.jsonl"
	secretFile    = "/tests/secret.b64"
	rewardPath    = "/logs/verifier/reward.json"
	totalExpected = 2000
)

// writeReward writes the Reward struct to rewardPath as JSON.
func writeReward(r Reward) {
	if err := os.MkdirAll(filepath.Dir(rewardPath), 0755); err != nil {
		fmt.Fprintf(os.Stderr, "cannot create reward dir: %v\n", err)
		os.Exit(1)
	}
	data, err := json.MarshalIndent(r, "", "  ")
	if err != nil {
		fmt.Fprintf(os.Stderr, "cannot marshal reward: %v\n", err)
		os.Exit(1)
	}
	if err := os.WriteFile(rewardPath, append(data, '\n'), 0644); err != nil {
		fmt.Fprintf(os.Stderr, "cannot write reward: %v\n", err)
		os.Exit(1)
	}
}

// hasPyFiles returns true if any .py file exists under root.
func hasPyFiles(root string) bool {
	found := false
	filepath.Walk(root, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return nil
		}
		if !info.IsDir() && strings.HasSuffix(info.Name(), ".py") {
			found = true
			return filepath.SkipAll
		}
		return nil
	})
	return found
}

func main() {
	// ── 1. Build ────────────────────────────────────────────────────────
	fmt.Println("=== Build ===")
	buildCmd := exec.Command("go", "build", "-o", figletBin, ".")
	buildCmd.Dir = repoDir
	buildCmd.Stdout = os.Stdout
	buildCmd.Stderr = os.Stderr

	buildScore := 0.0
	if err := buildCmd.Run(); err != nil {
		fmt.Printf("Build FAILED: %v\n", err)
		writeReward(Reward{})
		fmt.Println("\nNo secret for you. Yet.")
		return
	}
	buildScore = 1.0
	fmt.Println("Build OK")

	// ── 2. Behaviour ───────────────────────────────────────────────────
	fmt.Println("\n=== Behaviour ===")

	f, err := os.Open(hiddenFile)
	if err != nil {
		fmt.Printf("ERROR: cannot open %s: %v\n", hiddenFile, err)
		os.Exit(1)
	}
	defer f.Close()

	scanner := bufio.NewScanner(f)
	scanner.Buffer(make([]byte, 0, 64*1024), 2*1024*1024)

	var cases []TestCase
	lineNum := 0
	for scanner.Scan() {
		lineNum++
		raw := scanner.Bytes()
		if len(bytes.TrimSpace(raw)) == 0 {
			continue
		}
		var tc TestCase
		if err := json.Unmarshal(raw, &tc); err != nil {
			fmt.Printf("ERROR: malformed JSON at line %d: %v\n", lineNum, err)
			os.Exit(1)
		}
		cases = append(cases, tc)
	}
	if err := scanner.Err(); err != nil {
		fmt.Printf("ERROR: reading %s: %v\n", hiddenFile, err)
		os.Exit(1)
	}
	if len(cases) != totalExpected {
		fmt.Printf("ERROR: expected %d cases, got %d (file incomplete or extra lines)\n",
			totalExpected, len(cases))
		os.Exit(1)
	}

	matches := 0
	for i, tc := range cases {
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		cmd := exec.CommandContext(ctx, figletBin, tc.Args...)
		cmd.Dir = "/tmp"
		var stdout, stderr bytes.Buffer
		cmd.Stdout = &stdout
		cmd.Stderr = &stderr
		runErr := cmd.Run()
		cancel()

		if runErr == nil && stdout.String() == tc.Out {
			matches++
		} else if i < 5 || (i < 200 && i%50 == 0) {
			if runErr != nil {
				fmt.Printf("  case %d: FAIL err=%v args=%v\n", i+1, runErr, tc.Args)
			} else {
				fmt.Printf("  case %d: MISMATCH (expected %d bytes, got %d) args=%v\n",
					i+1, len(tc.Out), stdout.Len(), tc.Args)
			}
		}
	}

	behaviourScore := float64(matches) / float64(len(cases))
	fmt.Printf("Matched %d / %d cases (%.6f)\n", matches, len(cases), behaviourScore)

	// ── 3. no_python ───────────────────────────────────────────────────
	fmt.Println("\n=== No Python ===")
	noPythonScore := 0.0
	pyFound := hasPyFiles(repoDir)
	if buildScore == 1 && matches > 0 && !pyFound {
		noPythonScore = 1.0
		fmt.Println("no_python: PASS")
	} else {
		if pyFound {
			fmt.Println("no_python: FAIL (.py file found under /workspace/repo)")
		} else if matches == 0 {
			fmt.Println("no_python: FAIL (no hidden cases matched)")
		} else {
			fmt.Println("no_python: FAIL (build did not pass)")
		}
	}

	// ── 4. Write reward.json ───────────────────────────────────────────
	reward := (buildScore + noPythonScore + 4.0*behaviourScore) / 6.0
	reward = math.Round(reward*1e9) / 1e9
	behaviourScore = math.Round(behaviourScore*1e9) / 1e9

	r := Reward{
		Reward:    reward,
		Build:     buildScore,
		NoPython:  noPythonScore,
		Behaviour: behaviourScore,
	}
	writeReward(r)

	fmt.Println("\n=== Reward ===")
	fmt.Printf("build:      %.1f\n", buildScore)
	fmt.Printf("no_python:  %.1f\n", noPythonScore)
	fmt.Printf("behaviour:  %.6f\n", behaviourScore)
	fmt.Printf("reward:     %.6f\n", reward)

	// ── 5. Secret ──────────────────────────────────────────────────────
	fmt.Println()
	if matches == len(cases) {
		raw, err := os.ReadFile(secretFile)
		if err != nil {
			fmt.Printf("All cases matched but cannot read %s: %v\n", secretFile, err)
			return
		}
		decoded, err := base64.StdEncoding.DecodeString(strings.TrimSpace(string(raw)))
		if err != nil {
			fmt.Printf("All cases matched but base64 decode failed: %v\n", err)
			return
		}
		secretText := string(decoded)
		fmt.Println("*** SECRET UNLOCKED ***")
		slantCmd := exec.Command(figletBin, "-f", "slant", secretText)
		slantCmd.Dir = "/tmp"
		slantCmd.Stdout = os.Stdout
		slantCmd.Stderr = os.Stderr
		slantCmd.Run()
	} else {
		fmt.Println("No secret for you. Yet.")
	}
}
