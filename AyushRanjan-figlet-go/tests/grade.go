package main

import (
	"bufio"
	"bytes"
	"context"
	"encoding/base64"
	"encoding/json"
	"errors"
	"fmt"
	"io/fs"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"
)

const (
	repoPath     = "/workspace/repo"
	hiddenPath   = "/tests/hidden.jsonl"
	secretPath   = "/tests/secret.b64"
	figletBinary = "/tmp/figlet"
	rewardPath   = "/logs/verifier/reward.json"
	caseTimeout  = 5 * time.Second
)

type testCase struct {
	ID       string   `json:"id"`
	Argv     []string `json:"argv"`
	Stdout   string   `json:"stdout"`
	Stderr   string   `json:"stderr"`
	ExitCode int      `json:"exit_code"`
}

type rewardReport struct {
	Reward    float64 `json:"reward"`
	Build     float64 `json:"build"`
	NoPython  float64 `json:"no_python"`
	Behaviour float64 `json:"behaviour"`
}

func main() {
	report := rewardReport{}
	cliBuilt := false
	buildErr := runCommand(repoPath, "go", "build", "./...")
	if buildErr == nil {
		report.Build = 1
		if err := os.Remove(figletBinary); err != nil && !errors.Is(err, os.ErrNotExist) {
			fmt.Fprintf(os.Stderr, "could not clear old CLI binary: %v\n", err)
		} else if err := runCommand(repoPath, "go", "build", "-o", figletBinary, "."); err != nil {
			fmt.Fprintf(os.Stderr, "package build succeeded, but building the CLI binary failed: %v\n", err)
		} else {
			cliBuilt = true
		}
	} else {
		fmt.Fprintf(os.Stderr, "go build ./... failed: %v\n", buildErr)
	}

	cases, loadErr := loadCases(hiddenPath)
	matched := 0
	if loadErr != nil {
		fmt.Fprintf(os.Stderr, "could not load hidden cases: %v\n", loadErr)
	} else if report.Build == 1 && cliBuilt {
		matched = gradeCases(cases)
	} else if report.Build == 1 {
		fmt.Fprintln(os.Stderr, "CLI binary was not built; behavior score is zero")
	}
	if len(cases) > 0 {
		report.Behaviour = float64(matched) / float64(len(cases))
	}

	pythonFiles, scanErr := findPythonFiles(repoPath)
	if scanErr != nil {
		fmt.Fprintf(os.Stderr, "could not inspect solution files: %v\n", scanErr)
	} else if report.Build == 1 && len(pythonFiles) == 0 && matched > 0 {
		report.NoPython = 1
	}

	// Weights are build=1, no_python=1, behaviour=4, for a total of 6.
	report.Reward = (report.Build + report.NoPython + 4*report.Behaviour) / 6
	if err := writeReward(report); err != nil {
		fmt.Fprintf(os.Stderr, "could not write %s: %v\n", rewardPath, err)
	}
	fmt.Printf("build=%.3f no_python=%.3f behaviour=%.3f matched=%d/%d reward=%.3f\n",
		report.Build, report.NoPython, report.Behaviour, matched, len(cases), report.Reward)
	if scanErr == nil && len(pythonFiles) > 0 {
		fmt.Fprintf(os.Stderr, "Python files found in %s: %s\n", repoPath, strings.Join(pythonFiles, ", "))
	}

	if matched == len(cases) && len(cases) > 0 {
		unlockSecret()
	} else {
		fmt.Println("No secret for you. Yet.")
	}
}

func runCommand(dir, name string, args ...string) error {
	cmd := exec.Command(name, args...)
	cmd.Dir = dir
	var output bytes.Buffer
	cmd.Stdout = &output
	cmd.Stderr = &output
	if err := cmd.Run(); err != nil {
		if output.Len() > 0 {
			return fmt.Errorf("%w: %s", err, strings.TrimSpace(output.String()))
		}
		return err
	}
	return nil
}

func loadCases(path string) ([]testCase, error) {
	file, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer file.Close()

	var cases []testCase
	scanner := bufio.NewScanner(file)
	scanner.Buffer(make([]byte, 64*1024), 16*1024*1024)
	lineNumber := 0
	for scanner.Scan() {
		lineNumber++
		var item testCase
		if err := json.Unmarshal(scanner.Bytes(), &item); err != nil {
			return nil, fmt.Errorf("line %d: %w", lineNumber, err)
		}
		if item.ID == "" || item.Argv == nil {
			return nil, fmt.Errorf("line %d is missing id or argv", lineNumber)
		}
		cases = append(cases, item)
	}
	if err := scanner.Err(); err != nil {
		return nil, err
	}
	if len(cases) == 0 {
		return nil, errors.New("hidden case file is empty")
	}
	return cases, nil
}

func gradeCases(cases []testCase) int {
	matched := 0
	for index, item := range cases {
		ctx, cancel := context.WithTimeout(context.Background(), caseTimeout)
		cmd := exec.CommandContext(ctx, figletBinary, item.Argv...)
		var stdout, stderr bytes.Buffer
		cmd.Stdout = &stdout
		cmd.Stderr = &stderr
		err := cmd.Run()
		timedOut := errors.Is(ctx.Err(), context.DeadlineExceeded)
		cancel()

		exitCode := 0
		if err != nil {
			var exitErr *exec.ExitError
			if errors.As(err, &exitErr) {
				exitCode = exitErr.ExitCode()
			} else {
				exitCode = -1
			}
		}
		if !timedOut && stdout.String() == item.Stdout && stderr.String() == item.Stderr && exitCode == item.ExitCode {
			matched++
		} else if index < 10 {
			reason := "output mismatch"
			if timedOut {
				reason = "timed out after 5 seconds"
			} else if err != nil && exitCode == -1 {
				reason = err.Error()
			}
			fmt.Fprintf(os.Stderr, "case %s: %s (exit=%d expected=%d stdout=%d/%d bytes stderr=%d/%d bytes)\n",
				item.ID, reason, exitCode, item.ExitCode, stdout.Len(), len(item.Stdout), stderr.Len(), len(item.Stderr))
		}
		if (index+1)%250 == 0 {
			fmt.Printf("checked %d/%d hidden cases\n", index+1, len(cases))
		}
	}
	return matched
}

func findPythonFiles(root string) ([]string, error) {
	root = filepath.Clean(root)
	var found []string
	err := filepath.WalkDir(root, func(path string, entry fs.DirEntry, walkErr error) error {
		if walkErr != nil {
			return walkErr
		}
		if entry.IsDir() {
			cleanPath := filepath.Clean(path)
			if cleanPath == filepath.Join(root, ".git") {
				return filepath.SkipDir
			}
			return nil
		}
		if strings.EqualFold(filepath.Ext(entry.Name()), ".py") {
			relative, err := filepath.Rel(root, path)
			if err != nil {
				return err
			}
			found = append(found, relative)
		}
		return nil
	})
	return found, err
}

func writeReward(report rewardReport) error {
	if err := os.MkdirAll(filepath.Dir(rewardPath), 0o755); err != nil {
		return err
	}
	data, err := json.MarshalIndent(report, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(rewardPath, append(data, '\n'), 0o644)
}

func unlockSecret() {
	encoded, err := os.ReadFile(secretPath)
	if err != nil {
		fmt.Fprintf(os.Stderr, "behavior is perfect, but secret file is unavailable: %v\n", err)
		return
	}
	secret, err := base64.StdEncoding.DecodeString(strings.TrimSpace(string(encoded)))
	if err != nil {
		fmt.Fprintf(os.Stderr, "behavior is perfect, but secret file is not valid base64: %v\n", err)
		return
	}

	ctx, cancel := context.WithTimeout(context.Background(), caseTimeout)
	defer cancel()
	cmd := exec.CommandContext(ctx, figletBinary, "-f", "slant", string(secret))
	output, err := cmd.CombinedOutput()
	if err != nil {
		if errors.Is(ctx.Err(), context.DeadlineExceeded) {
			fmt.Fprintln(os.Stderr, "secret rendering timed out")
		} else {
			fmt.Fprintf(os.Stderr, "secret rendering failed: %v\n", err)
		}
		return
	}
	fmt.Println("*** SECRET UNLOCKED ***")
	fmt.Print(string(output))
}
