// Grader for the figlet-go task. Go standard library only (the room has no
// Python). Run by test.sh as: cd /tests && go run grade.go
//
//	build     (weight 1): `go build -o /tmp/figlet .` works in /workspace/repo
//	                      and go.mod has no `require` lines
//	no_python (weight 1): build passed AND no .py file under /workspace/repo
//	                      AND at least one hidden case is right
//	behaviour (weight 4): share of hidden cases whose stdout is exactly "out"
//
// reward = (build + no_python + 4*behaviour) / 6, written to
// /logs/verifier/reward.json. A perfect twin also draws the secret.
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
	"time"
)

const (
	repo   = "/workspace/repo"
	binary = "/tmp/figlet"
	cases  = "/tests/data/hidden.jsonl"
	secret = "/tests/secret.b64"
	output = "/logs/verifier/reward.json"
)

type testCase struct {
	Args []string `json:"args"`
	Out  string   `json:"out"`
}

func build() float64 {
	os.Remove(binary) // never grade a binary the agent left behind
	goMod, err := os.ReadFile(filepath.Join(repo, "go.mod"))
	if err != nil {
		fmt.Println("build: no go.mod")
		return 0
	}
	for _, line := range strings.Split(string(goMod), "\n") {
		if strings.HasPrefix(strings.TrimSpace(line), "require") {
			fmt.Println("build: go.mod has a require line (standard library only)")
			return 0
		}
	}
	cmd := exec.Command("go", "build", "-o", binary, ".")
	cmd.Dir = repo
	if out, err := cmd.CombinedOutput(); err != nil {
		fmt.Printf("build: failed\n%s\n", out)
		return 0
	}
	return 1
}

func pythonFiles() int {
	n := 0
	filepath.WalkDir(repo, func(p string, d fs.DirEntry, err error) error {
		if err == nil && !d.IsDir() && strings.HasSuffix(p, ".py") {
			n++
		}
		return nil
	})
	return n
}

func runFiglet(dir string, args []string) []byte {
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	cmd := exec.CommandContext(ctx, binary, args...)
	cmd.Dir = dir // not the repo: the program must work from anywhere
	var stdout bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Run()
	if ctx.Err() != nil {
		return nil
	}
	return stdout.Bytes()
}

func behaviour() (float64, int) {
	f, err := os.Open(cases)
	if err != nil {
		fmt.Println("behaviour: cannot read hidden cases:", err)
		os.Exit(1)
	}
	defer f.Close()
	var all []testCase
	sc := bufio.NewScanner(f)
	sc.Buffer(make([]byte, 1<<20), 1<<24)
	for sc.Scan() {
		var c testCase
		if err := json.Unmarshal(sc.Bytes(), &c); err != nil {
			fmt.Println("behaviour: bad case line:", err)
			os.Exit(1)
		}
		all = append(all, c)
	}
	dir, _ := os.MkdirTemp("", "figlet-cwd-")
	defer os.RemoveAll(dir)

	ok := make([]bool, len(all))
	var wg sync.WaitGroup
	jobs := make(chan int)
	for w := 0; w < 4; w++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for i := range jobs {
				ok[i] = string(runFiglet(dir, all[i].Args)) == all[i].Out
			}
		}()
	}
	for i := range all {
		jobs <- i
	}
	close(jobs)
	wg.Wait()

	right, shown := 0, 0
	for i, good := range ok {
		if good {
			right++
		} else if shown < 3 {
			fmt.Printf("behaviour: wrong output for args %q\n", all[i].Args)
			shown++
		}
	}
	return float64(right) / float64(len(all)), right
}

func main() {
	b := build()
	beh, right := 0.0, 0
	if b == 1 {
		beh, right = behaviour()
	}
	noPy := 0.0
	if b == 1 && pythonFiles() == 0 && right >= 1 {
		noPy = 1
	}
	reward := (1*b + 1*noPy + 4*beh) / 6

	os.MkdirAll(filepath.Dir(output), 0o777)
	data, _ := json.Marshal(map[string]float64{
		"reward": reward, "build": b, "no_python": noPy, "behaviour": beh,
	})
	if err := os.WriteFile(output, data, 0o644); err != nil {
		fmt.Println("cannot write reward:", err)
		os.Exit(1)
	}
	fmt.Printf("build=%v no_python=%v behaviour=%.4f (%d right) reward=%.4f\n", b, noPy, beh, right, reward)

	if beh == 1.0 {
		raw, _ := os.ReadFile(secret)
		text, err := base64.StdEncoding.DecodeString(strings.TrimSpace(string(raw)))
		if err == nil {
			fmt.Println("*** SECRET UNLOCKED ***")
			os.Stdout.Write(runFiglet(os.TempDir(), []string{"-f", "slant", string(text)}))
			return
		}
	}
	fmt.Println("No secret for you. Yet.")
}
