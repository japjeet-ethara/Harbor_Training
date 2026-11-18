// grade.go scores a Go twin of pyfiglet. Standard library only, no network.
//
//	build      (weight 1): `go build ./...` and `go build -o /tmp/figlet .` pass
//	no_python  (weight 1): build passed, no .py file is left in the repository,
//	                       and at least one hidden case matches
//	behaviour  (weight 4): share of hidden cases whose stdout matches exactly
//
// It writes /logs/verifier/reward.json. When behaviour is exactly 1.0 it asks
// the twin itself to draw the secret in /tests/secret.b64.
package main

import (
	"bufio"
	"bytes"
	"context"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"io/fs"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"sync"
	"syscall"
	"time"
)

const (
	repo       = "/workspace/repo"
	binary     = "/tmp/figlet"
	hiddenFile = "/tests/data/hidden.jsonl"
	secretFile = "/tests/secret.b64"
	rewardFile = "/logs/verifier/reward.json"
	caseTime   = 5 * time.Second
	buildTime  = 10 * time.Minute
	workers    = 4
	// The twin runs as "nobody", so it cannot read /tests (mode 0700, root).
	runUID = 65534
	runGID = 65534
)

type testCase struct {
	Args []string `json:"args"`
	Out  string   `json:"out"`
}

func goBuild(args ...string) bool {
	ctx, cancel := context.WithTimeout(context.Background(), buildTime)
	defer cancel()
	cmd := exec.CommandContext(ctx, "go", args...)
	cmd.Dir = repo
	out, err := cmd.CombinedOutput()
	if err != nil {
		fmt.Printf("$ go %s\n%s(%v)\n", strings.Join(args, " "), out, err)
		return false
	}
	return true
}

// runTwin runs the built program as an unprivileged user from "/".
func runTwin(args []string) ([]byte, error) {
	ctx, cancel := context.WithTimeout(context.Background(), caseTime)
	defer cancel()
	cmd := exec.CommandContext(ctx, binary, args...)
	cmd.Dir = "/"
	cmd.Env = []string{"PATH=/usr/local/bin:/usr/bin:/bin", "HOME=/nonexistent", "LANG=C.UTF-8"}
	cmd.SysProcAttr = &syscall.SysProcAttr{
		Credential: &syscall.Credential{Uid: runUID, Gid: runGID},
		Setpgid:    true,
	}
	var stdout bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Cancel = func() error { return syscall.Kill(-cmd.Process.Pid, syscall.SIGKILL) }
	cmd.WaitDelay = time.Second
	err := cmd.Run()
	return stdout.Bytes(), err
}

func pyFiles() []string {
	var found []string
	filepath.WalkDir(repo, func(path string, d fs.DirEntry, err error) error {
		if err == nil && !d.IsDir() && strings.HasSuffix(path, ".py") {
			found = append(found, path)
		}
		return nil
	})
	return found
}

func loadCases(path string) ([]testCase, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	var cases []testCase
	sc := bufio.NewScanner(f)
	sc.Buffer(make([]byte, 1<<20), 16<<20)
	for sc.Scan() {
		line := strings.TrimSpace(sc.Text())
		if line == "" {
			continue
		}
		var c testCase
		if err := json.Unmarshal([]byte(line), &c); err != nil {
			return nil, err
		}
		cases = append(cases, c)
	}
	return cases, sc.Err()
}

func writeReward(reward, build, noPython, behaviour float64) {
	os.MkdirAll(filepath.Dir(rewardFile), 0o755)
	data, _ := json.Marshal(map[string]float64{
		"reward": reward, "build": build, "no_python": noPython, "behaviour": behaviour,
	})
	if err := os.WriteFile(rewardFile, data, 0o644); err != nil {
		fmt.Println("cannot write reward:", err)
		os.Exit(1)
	}
	fmt.Println(string(data))
}

func main() {
	cases, err := loadCases(hiddenFile)
	if err != nil || len(cases) == 0 {
		fmt.Println("cannot load hidden cases:", err)
		os.Exit(1)
	}

	// 1. build
	os.RemoveAll(binary)
	build := 0.0
	if goBuild("build", "./...") && goBuild("build", "-o", binary, ".") {
		build = 1.0
	}
	fmt.Printf("build: %.0f\n", build)

	// 3. behaviour (run before no_python, which depends on it)
	matched := 0
	if build == 1.0 {
		results := make([]bool, len(cases))
		jobs := make(chan int)
		var wg sync.WaitGroup
		for w := 0; w < workers; w++ {
			wg.Add(1)
			go func() {
				defer wg.Done()
				for i := range jobs {
					out, err := runTwin(cases[i].Args)
					results[i] = err == nil && string(out) == cases[i].Out
				}
			}()
		}
		for i := range cases {
			jobs <- i
		}
		close(jobs)
		wg.Wait()
		shown := 0
		for i, ok := range results {
			if ok {
				matched++
			} else if shown < 3 {
				shown++
				a, _ := json.Marshal(cases[i].Args)
				fmt.Printf("mismatch, hidden case %d: args %s\n", i, a)
			}
		}
	}
	behaviour := float64(matched) / float64(len(cases))
	fmt.Printf("behaviour: %d/%d = %.4f\n", matched, len(cases), behaviour)

	// 2. no_python
	noPython := 0.0
	left := pyFiles()
	if build == 1.0 && len(left) == 0 && matched > 0 {
		noPython = 1.0
	}
	fmt.Printf("no_python: %.0f (%d .py files left, %d cases matched)\n", noPython, len(left), matched)

	// 4. reward
	reward := (1*build + 1*noPython + 4*behaviour) / 6
	writeReward(reward, build, noPython, behaviour)

	// 5. the secret, drawn by the twin itself
	fmt.Println()
	if matched == len(cases) {
		raw, err := os.ReadFile(secretFile)
		if err == nil {
			var text []byte
			text, err = base64.StdEncoding.DecodeString(strings.TrimSpace(string(raw)))
			if err == nil {
				var art []byte
				art, err = runTwin([]string{"-f", "slant", string(text)})
				fmt.Println("*** SECRET UNLOCKED ***")
				fmt.Print(string(art))
			}
		}
		if err != nil {
			fmt.Println("secret error:", err)
		}
	} else {
		fmt.Println("No secret for you. Yet.")
	}
}
