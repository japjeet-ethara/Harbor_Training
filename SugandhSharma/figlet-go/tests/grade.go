// grade.go is the examiner of the figlet-go task. tests/test.sh runs it:  cd /tests && go run grade.go
//
// Three checks, combined as a weighted mean into /logs/verifier/reward.json:
//
//	build      weight 1   "go build ./..." and "go build -o /tmp/figlet ." both pass in /workspace/repo
//	no_python  weight 1   the build passed AND no .py file is left under /workspace/repo AND the font
//	                      files the cases use are still inside /workspace/repo AND at least one hidden
//	                      case is right
//	behaviour  weight 4   share of the hidden cases whose standard output equals the frozen answer exactly
//
// A perfect twin (behaviour exactly 1.0) is shown the secret, drawn by the twin itself.
// Only the Go standard library is used, and nothing is downloaded.
package main

import (
	"bufio"
	"bytes"
	"context"
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

const (
	repo        = "/workspace/repo"
	program     = "/tmp/figlet"
	hiddenCases = "/tests/data/hidden.jsonl"
	secretFile  = "/tests/secret.b64"
	rewardFile  = "/logs/verifier/reward.json"
	caseTimeout = 5 * time.Second
)

type testCase struct {
	Args []string `json:"args"`
	Out  string   `json:"out"`
}

func loadCases() []testCase {
	file, err := os.Open(hiddenCases)
	if err != nil {
		fmt.Println("cannot read the cases:", err)
		os.Exit(2) // no reward is written: the run counts as a verifier error, not as a 0
	}
	defer file.Close()
	var cases []testCase
	lines := bufio.NewScanner(file)
	lines.Buffer(make([]byte, 1024*1024), 64*1024*1024)
	for lines.Scan() {
		var c testCase
		if err := json.Unmarshal(lines.Bytes(), &c); err != nil {
			fmt.Println("bad case line:", err)
			os.Exit(2)
		}
		cases = append(cases, c)
	}
	if len(cases) == 0 {
		fmt.Println("no cases found")
		os.Exit(2)
	}
	return cases
}

// goBuild runs one "go build" in the repository: offline, with the toolchain of the image.
func goBuild(args ...string) bool {
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Minute)
	defer cancel()
	cmd := exec.CommandContext(ctx, "go", append([]string{"build"}, args...)...)
	cmd.Dir = repo
	cmd.Env = append(os.Environ(), "GOFLAGS=-mod=mod", "GOPROXY=off", "GOTOOLCHAIN=local", "CGO_ENABLED=0")
	out, err := cmd.CombinedOutput()
	if err != nil {
		fmt.Printf("go build %s failed: %v\n%s\n", strings.Join(args, " "), err, lastLines(string(out), 15))
		return false
	}
	return true
}

func lastLines(s string, n int) string {
	lines := strings.Split(strings.TrimRight(s, "\n"), "\n")
	if len(lines) > n {
		lines = lines[len(lines)-n:]
	}
	return strings.Join(lines, "\n")
}

func buildPasses() bool {
	if _, err := os.Stat(filepath.Join(repo, "go.mod")); err != nil {
		fmt.Println("there is no go.mod in", repo)
		return false
	}
	os.Remove(program)
	if !goBuild("./...") || !goBuild("-o", program, ".") {
		return false
	}
	st, err := os.Stat(program)
	return err == nil && st.Mode().IsRegular()
}

// runCase starts the twin in another working directory and returns what it wrote to standard output.
func runCase(args []string) (string, bool) {
	ctx, cancel := context.WithTimeout(context.Background(), caseTimeout)
	defer cancel()
	cmd := exec.CommandContext(ctx, program, args...)
	cmd.Dir = "/"
	cmd.WaitDelay = time.Second
	var stdout bytes.Buffer
	cmd.Stdout = &stdout
	if err := cmd.Start(); err != nil {
		return "", false
	}
	cmd.Wait()
	return stdout.String(), ctx.Err() == nil
}

// filesUnder lists the lower-cased base names of all files under the repository.
func filesUnder(root string) map[string]bool {
	names := map[string]bool{}
	filepath.WalkDir(root, func(path string, d fs.DirEntry, err error) error {
		if err == nil && !d.IsDir() {
			names[strings.ToLower(d.Name())] = true
		}
		return nil
	})
	return names
}

func fontOf(args []string) string {
	for i := 0; i+1 < len(args); i++ {
		if args[i] == "-f" {
			return args[i+1]
		}
	}
	return "standard"
}

func round4(x float64) float64 { return math.Round(x*10000) / 10000 }

func main() {
	cases := loadCases()

	build := 0.0
	if buildPasses() {
		build = 1
	}

	right := 0
	if build == 1 {
		for _, c := range cases {
			if out, inTime := runCase(c.Args); inTime && out == c.Out {
				right++
			}
		}
	}
	behaviour := float64(right) / float64(len(cases))

	noPython := 0.0
	if build == 1 && right >= 1 {
		names := filesUnder(repo)
		clean := true
		for name := range names {
			if strings.HasSuffix(name, ".py") {
				fmt.Println("a .py file is still in the repository:", name)
				clean = false
				break
			}
		}
		for _, c := range cases {
			font := strings.ToLower(fontOf(c.Args))
			if clean && !names[font+".flf"] && !names[font+".tlf"] {
				fmt.Println("the font file is no longer in the repository:", font)
				clean = false
			}
		}
		if clean {
			noPython = 1
		}
	}

	reward := (1*build + 1*noPython + 4*behaviour) / 6
	result := map[string]float64{"reward": round4(reward), "build": build, "no_python": noPython,
		"behaviour": round4(behaviour)}
	text, _ := json.MarshalIndent(result, "", "  ")
	if err := os.MkdirAll(filepath.Dir(rewardFile), 0o755); err != nil {
		fmt.Println("cannot make the reward folder:", err)
		os.Exit(2)
	}
	if err := os.WriteFile(rewardFile, append(text, '\n'), 0o644); err != nil {
		fmt.Println("cannot write the reward:", err)
		os.Exit(2)
	}
	fmt.Printf("build %v, no_python %v, behaviour %d of %d cases right, reward %v\n",
		build, noPython, right, len(cases), round4(reward))

	// The secret: only a twin that is right on every case draws it, and it draws it itself.
	if right == len(cases) {
		encoded, err := os.ReadFile(secretFile)
		message, err2 := base64.StdEncoding.DecodeString(strings.TrimSpace(string(encoded)))
		if err == nil && err2 == nil {
			banner, _ := runCase([]string{"-f", "slant", string(message)})
			fmt.Println("*** SECRET UNLOCKED ***")
			fmt.Print(banner)
			return
		}
	}
	fmt.Println("No secret for you. Yet.")
}
