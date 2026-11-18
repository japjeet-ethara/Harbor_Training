package main

import (
	"bufio"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"io/fs"
	"math"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"
)

// TestCase represents one line from visible.jsonl or hidden.jsonl.
type TestCase struct {
	Args []string `json:"args"`
	Out  string   `json:"out"`
}

// Reward is written to /logs/verifier/reward.json.
type Reward struct {
	Reward    float64 `json:"reward"`
	Build     float64 `json:"build"`
	NoPython  float64 `json:"no_python"`
	Behaviour float64 `json:"behaviour"`
}

func main() {
	// ---------- 1. build ----------
	buildScore := 0.0
	cmd := exec.Command("go", "build", "-o", "/tmp/figlet", ".")
	cmd.Dir = "/workspace/repo"
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	if err := cmd.Run(); err != nil {
		fmt.Println("BUILD FAILED:", err)
	} else {
		buildScore = 1.0
		fmt.Println("BUILD OK")
	}

	// ---------- 2. no_python ----------
	noPythonScore := 0.0
	hasPy := false
	filepath.WalkDir("/workspace/repo", func(path string, d fs.DirEntry, err error) error {
		if err != nil {
			return nil
		}
		if !d.IsDir() && strings.HasSuffix(d.Name(), ".py") {
			hasPy = true
			return filepath.SkipAll
		}
		return nil
	})

	// ---------- 3. behaviour ----------
	behaviourScore := 0.0
	if buildScore == 1.0 {
		cases, err := loadCases("/tests/data/hidden.jsonl")
		if err != nil {
			fmt.Println("LOAD HIDDEN CASES ERROR:", err)
		} else {
			correct := 0
			for i, tc := range cases {
				actual, ok := runFiglet(tc.Args)
				if ok && actual == tc.Out {
					correct++
				}
				if (i+1)%200 == 0 || i+1 == len(cases) {
					fmt.Printf("behaviour: %d/%d checked, %d correct\n", i+1, len(cases), correct)
				}
			}
			if len(cases) > 0 {
				behaviourScore = float64(correct) / float64(len(cases))
			}
		}

		// no_python: requires build AND no .py files AND at least one hidden case correct
		if !hasPy && behaviourScore > 0 {
			noPythonScore = 1.0
		}
	}

	// ---------- 4. weighted mean ----------
	// build=1, no_python=1, behaviour=4  → total weight 6
	reward := (buildScore*1 + noPythonScore*1 + behaviourScore*4) / 6.0
	// Round to 6 decimal places to avoid floating-point noise
	reward = math.Round(reward*1e6) / 1e6

	fmt.Printf("\nbuild=%.2f  no_python=%.2f  behaviour=%.4f  reward=%.4f\n",
		buildScore, noPythonScore, behaviourScore, reward)

	// ---------- write reward.json ----------
	os.MkdirAll("/logs/verifier", 0o755)
	r := Reward{
		Reward:    reward,
		Build:     buildScore,
		NoPython:  noPythonScore,
		Behaviour: behaviourScore,
	}
	data, _ := json.MarshalIndent(r, "", "  ")
	os.WriteFile("/logs/verifier/reward.json", data, 0o644)

	// ---------- 5. secret ----------
	if behaviourScore == 1.0 {
		secretB64, err := os.ReadFile("/tests/secret.b64")
		if err != nil {
			fmt.Println("Could not read secret.b64:", err)
		} else {
			decoded, err := base64.StdEncoding.DecodeString(strings.TrimSpace(string(secretB64)))
			if err != nil {
				fmt.Println("Could not decode secret:", err)
			} else {
				out, err := exec.Command("/tmp/figlet", "-f", "slant", string(decoded)).Output()
				if err != nil {
					fmt.Println("Could not render secret:", err)
				} else {
					fmt.Println("\n*** SECRET UNLOCKED ***")
					fmt.Print(string(out))
				}
			}
		}
	} else {
		fmt.Println("\nNo secret for you. Yet.")
	}
}

func loadCases(path string) ([]TestCase, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	var cases []TestCase
	scanner := bufio.NewScanner(f)
	scanner.Buffer(make([]byte, 0, 1024*1024), 10*1024*1024)
	for scanner.Scan() {
		var tc TestCase
		if err := json.Unmarshal(scanner.Bytes(), &tc); err != nil {
			return nil, err
		}
		cases = append(cases, tc)
	}
	return cases, scanner.Err()
}

func runFiglet(args []string) (string, bool) {
	ctx := exec.Command("/tmp/figlet", args...)
	ctx.Dir = "/workspace/repo"

	done := make(chan error, 1)
	var out []byte
	go func() {
		var err error
		out, err = ctx.Output()
		done <- err
	}()

	select {
	case err := <-done:
		if err != nil {
			return "", false
		}
		return string(out), true
	case <-time.After(5 * time.Second):
		ctx.Process.Kill()
		return "", false
	}
}
