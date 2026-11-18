// grade.go — verifier for the pyfiglet Go port task.
//
// Run with: cd /tests && go run grade.go
// Standard library only; needs no network.
//
// Scores (weights):
//   build      (1): `go build -o /tmp/figlet .` succeeds in /workspace/repo
//   no_python  (1): build passed AND no .py file under /workspace/repo
//                   AND at least one hidden case matches
//   behaviour  (4): share of hidden cases whose stdout equals "out" exactly
//
// Writes /logs/verifier/reward.json with the weighted mean and sub-scores.
package main

import (
	"bytes"
	"context"
	"encoding/base64"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"io/fs"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
	"sync"
	"time"
)

const (
	repoDir     = "/workspace/repo"
	binPath     = "/tmp/figlet"
	hiddenPath  = "/tests/data/hidden.jsonl"
	secretPath  = "/tests/secret.b64"
	rewardPath  = "/logs/verifier/reward.json"
	caseTimeout = 5 * time.Second
	buildLimit  = 5 * time.Minute
)

type testCase struct {
	Args []string `json:"args"`
	Out  string   `json:"out"`
}

func main() {
	build := 0.0
	noPython := 0.0
	behaviour := 0.0

	if runBuild() {
		build = 1.0
	}

	if build == 1.0 {
		cases, err := loadCases(hiddenPath)
		if err != nil {
			fmt.Printf("[grade] cannot load hidden cases: %v\n", err)
		} else {
			passed := runCases(cases)
			if len(cases) > 0 {
				behaviour = float64(passed) / float64(len(cases))
			}
			fmt.Printf("[grade] behaviour: %d/%d = %.4f\n", passed, len(cases), behaviour)

			pyFiles := findPyFiles(repoDir)
			if len(pyFiles) > 0 {
				fmt.Printf("[grade] no_python: found %d .py file(s), e.g. %s\n", len(pyFiles), pyFiles[0])
			} else if passed == 0 {
				fmt.Println("[grade] no_python: no .py files, but no hidden case matches -> 0")
			} else {
				noPython = 1.0
			}
		}
	}

	reward := (1*build + 1*noPython + 4*behaviour) / 6
	writeReward(reward, build, noPython, behaviour)
	fmt.Printf("[grade] build=%.0f no_python=%.0f behaviour=%.4f reward=%.4f\n",
		build, noPython, behaviour, reward)

	if behaviour == 1.0 {
		printSecret()
	} else {
		fmt.Println("No secret for you. Yet.")
	}
}

// runBuild checks the build rules from instruction.md: Go standard library
// only (no require directives in go.mod), `go build ./...` passes, and
// `go build -o /tmp/figlet .` produces the program.
func runBuild() bool {
	_ = os.Remove(binPath)

	if mod, err := os.ReadFile(filepath.Join(repoDir, "go.mod")); err == nil {
		for _, line := range strings.Split(string(mod), "\n") {
			fields := strings.Fields(line)
			if len(fields) > 0 && fields[0] == "require" {
				fmt.Println("[grade] build FAILED: go.mod requires external modules (standard library only)")
				return false
			}
		}
	}

	for _, args := range [][]string{
		{"build", "./..."},
		{"build", "-o", binPath, "."},
	} {
		ctx, cancel := context.WithTimeout(context.Background(), buildLimit)
		cmd := exec.CommandContext(ctx, "go", args...)
		cmd.Dir = repoDir
		out, err := cmd.CombinedOutput()
		cancel()
		if err != nil {
			fmt.Printf("[grade] build FAILED (go %s): %v\n%s\n", strings.Join(args, " "), err, out)
			return false
		}
	}
	fmt.Println("[grade] build OK")
	return true
}

func loadCases(path string) ([]testCase, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	var cases []testCase
	dec := json.NewDecoder(f)
	for {
		var c testCase
		if err := dec.Decode(&c); errors.Is(err, io.EOF) {
			break
		} else if err != nil {
			return nil, err
		}
		cases = append(cases, c)
	}
	return cases, nil
}

// runFiglet returns stdout, or ok=false on timeout or failure to start.
func runFiglet(args []string) (string, bool) {
	ctx, cancel := context.WithTimeout(context.Background(), caseTimeout)
	defer cancel()
	cmd := exec.CommandContext(ctx, binPath, args...)
	var stdout bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Stderr = io.Discard
	err := cmd.Run()
	if ctx.Err() != nil {
		return "", false
	}
	var exitErr *exec.ExitError
	if err != nil && !errors.As(err, &exitErr) {
		return "", false
	}
	return stdout.String(), true
}

func runCases(cases []testCase) int {
	workers := runtime.NumCPU()
	if workers < 1 {
		workers = 1
	}
	jobs := make(chan int)
	results := make([]bool, len(cases))
	var wg sync.WaitGroup
	for w := 0; w < workers; w++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for i := range jobs {
				got, ok := runFiglet(cases[i].Args)
				results[i] = ok && got == cases[i].Out
			}
		}()
	}
	for i := range cases {
		jobs <- i
	}
	close(jobs)
	wg.Wait()

	passed := 0
	shown := 0
	for i, ok := range results {
		if ok {
			passed++
		} else if shown < 5 {
			shown++
			fmt.Printf("[grade] FAIL hidden case %d\n", i)
		}
	}
	return passed
}

func findPyFiles(root string) []string {
	var found []string
	_ = filepath.WalkDir(root, func(path string, d fs.DirEntry, err error) error {
		if err != nil {
			return nil
		}
		if !d.IsDir() && strings.HasSuffix(d.Name(), ".py") {
			found = append(found, path)
		}
		return nil
	})
	return found
}

func writeReward(reward, build, noPython, behaviour float64) {
	if err := os.MkdirAll(filepath.Dir(rewardPath), 0o755); err != nil {
		fmt.Printf("[grade] cannot create log dir: %v\n", err)
		return
	}
	data, _ := json.Marshal(map[string]float64{
		"reward":    reward,
		"build":     build,
		"no_python": noPython,
		"behaviour": behaviour,
	})
	if err := os.WriteFile(rewardPath, data, 0o644); err != nil {
		fmt.Printf("[grade] cannot write reward: %v\n", err)
	}
}

func printSecret() {
	raw, err := os.ReadFile(secretPath)
	if err != nil {
		fmt.Printf("[grade] cannot read secret: %v\n", err)
		return
	}
	text, err := base64.StdEncoding.DecodeString(strings.TrimSpace(string(raw)))
	if err != nil {
		fmt.Printf("[grade] cannot decode secret: %v\n", err)
		return
	}
	out, _ := runFiglet([]string{"-f", "slant", string(text)})
	fmt.Println("*** SECRET UNLOCKED ***")
	fmt.Print(out)
}
