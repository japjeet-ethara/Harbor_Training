package main

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"strings"
	"syscall"
	"time"
)

type scores struct {
	Build     float64 `json:"build"`
	NoPython  float64 `json:"no_python"`
	Behaviour float64 `json:"behaviour"`
	Reward    float64 `json:"reward"`
}

var forbiddenImports = []*regexp.Regexp{
	regexp.MustCompile(`(?m)["\x60](os/exec|syscall|plugin|unsafe|C|net(?:/.*)?)[\x60"]`),
}

func runGo(repo string, args ...string) error {
	cmd := exec.Command("go", args...)
	cmd.Dir = repo
	cmd.Env = append(os.Environ(),
		"GOTOOLCHAIN=local", "GOPROXY=off", "GOFLAGS=-mod=mod", "CGO_ENABLED=0",
		"GOCACHE=/tmp/gocache", "HOME=/tmp")
	out, err := cmd.CombinedOutput()
	if err != nil {
		fmt.Printf("build: failed: %v\n%s", err, out)
	}
	return err
}

func checkBuild(repo string) float64 {
	mod, err := os.ReadFile(filepath.Join(repo, "go.mod"))
	if err != nil {
		fmt.Println("build: go.mod is missing")
		return 0
	}
	for _, line := range strings.Split(string(mod), "\n") {
		fields := strings.Fields(line)
		if len(fields) > 0 && (fields[0] == "require" || fields[0] == "replace") {
			fmt.Println("build: forbidden module directive")
			return 0
		}
	}
	err = filepath.Walk(repo, func(path string, info os.FileInfo, err error) error {
		if err != nil || info.IsDir() || !strings.HasSuffix(path, ".go") {
			return err
		}
		src, readErr := os.ReadFile(path)
		if readErr != nil {
			return readErr
		}
		for _, forbidden := range forbiddenImports {
			if forbidden.Match(src) {
				return fmt.Errorf("forbidden import in %s", path)
			}
		}
		return nil
	})
	if err != nil {
		fmt.Printf("build: %v\n", err)
		return 0
	}
	if runGo(repo, "build", "./...") != nil {
		return 0
	}
	if runGo(repo, "build", "-o", "/tmp/titlecase", ".") != nil {
		return 0
	}
	fmt.Println("build: ok")
	return 1
}

func checkNoPython(repo string, behaviour float64) float64 {
	found := false
	err := filepath.Walk(repo, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}
		if !info.IsDir() && strings.HasSuffix(info.Name(), ".py") {
			found = true
		}
		return nil
	})
	if err != nil || found {
		fmt.Println("no_python: Python files remain")
		return 0
	}
	if behaviour < 0.5 {
		fmt.Println("no_python: behaviour threshold not met")
		return 0
	}
	fmt.Println("no_python: ok")
	return 1
}

func checkBehaviour(dataDir string) float64 {
	titles, err := os.ReadFile(filepath.Join(dataDir, "titles.txt"))
	if err != nil {
		fmt.Println("behaviour: titles missing")
		return 0
	}
	rawAnswers, err := os.ReadFile(filepath.Join(dataDir, "answers.txt"))
	if err != nil {
		fmt.Println("behaviour: answers missing")
		return 0
	}
	answers := bytes.Split(bytes.TrimSuffix(rawAnswers, []byte("\n")), []byte("\n"))

	_ = os.Chmod("/tests", 0700)
	binary := "/tmp/titlecase-hardened"
	if err := os.Remove(binary); err != nil && !os.IsNotExist(err) {
		return 0
	}
	src, err := os.ReadFile("/tmp/titlecase")
	if err != nil {
		fmt.Println("behaviour: binary missing")
		return 0
	}
	if err := os.WriteFile(binary, src, 0755); err != nil {
		fmt.Println("behaviour: cannot stage binary")
		return 0
	}

	ctx, cancel := context.WithTimeout(context.Background(), 120*time.Second)
	defer cancel()
	cmd := exec.CommandContext(ctx, binary)
	cmd.Dir = "/tmp"
	cmd.Stdin = bytes.NewReader(titles)
	var stdout, stderr bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Stderr = &stderr
	cmd.SysProcAttr = &syscall.SysProcAttr{
		Credential: &syscall.Credential{Uid: 65534, Gid: 65534},
	}
	err = cmd.Run()
	if ctx.Err() == context.DeadlineExceeded {
		fmt.Println("behaviour: timeout")
		return 0
	}
	if err != nil {
		fmt.Printf("behaviour: exit status: %v %s\n", err, stderr.String())
		return 0
	}
	produced := bytes.Split(bytes.TrimSuffix(stdout.Bytes(), []byte("\n")), []byte("\n"))
	matched := 0
	for i, want := range answers {
		if i < len(produced) && bytes.Equal(produced[i], want) {
			matched++
		}
	}
	fmt.Printf("behaviour: %d of %d lines match (%d lines produced)\n", matched, len(answers), len(produced))
	return float64(matched) / float64(len(answers))
}

func main() {
	if len(os.Args) != 4 {
		fmt.Println("usage: grade.go repo data_dir reward_json")
		os.Exit(1)
	}
	result := scores{}
	result.Build = checkBuild(os.Args[1])
	if result.Build == 1 {
		result.Behaviour = checkBehaviour(os.Args[2])
		result.NoPython = checkNoPython(os.Args[1], result.Behaviour)
	}
	result.Reward = (result.Build + result.NoPython + 4*result.Behaviour) / 6
	result.Build = round(result.Build)
	result.NoPython = round(result.NoPython)
	result.Behaviour = round(result.Behaviour)
	result.Reward = round(result.Reward)
	if err := os.MkdirAll(filepath.Dir(os.Args[3]), 0755); err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
	data, _ := json.MarshalIndent(result, "", "  ")
	_ = os.WriteFile(os.Args[3], data, 0644)
	fmt.Println(string(data))
}

func round(v float64) float64 {
	return float64(int(v*10000+0.5)) / 10000
}
