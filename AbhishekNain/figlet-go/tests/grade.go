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
	candidateRepo  = "/workspace/repo"
	hiddenDataPath = "/tests/data/hidden.jsonl"
	candidateExe   = "/tmp/figlet"
	rewardPath     = "/logs/verifier/reward.json"
	secretPath     = "/tests/secret.b64"
	expectedCases  = 2000
)

type TestCase struct {
	Args []string
	Out  string
}

type RewardOutput struct {
	Reward    float64 `json:"reward"`
	Build     float64 `json:"build"`
	NoPython  float64 `json:"no_python"`
	Behaviour float64 `json:"behaviour"`
}

func writeRewardFile(path string, reward, build, noPython, behaviour float64) error {
	dir := filepath.Dir(path)
	if err := os.MkdirAll(dir, 0755); err != nil {
		return fmt.Errorf("failed to create reward directory %s: %w", dir, err)
	}

	out := RewardOutput{
		Reward:    reward,
		Build:     build,
		NoPython:  noPython,
		Behaviour: behaviour,
	}

	data, err := json.MarshalIndent(out, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal reward JSON: %w", err)
	}
	data = append(data, '\n')

	tmpPath := path + ".tmp"
	if err := os.WriteFile(tmpPath, data, 0644); err != nil {
		return fmt.Errorf("failed to write temp reward file: %w", err)
	}
	if err := os.Rename(tmpPath, path); err != nil {
		return fmt.Errorf("failed to move reward file to destination: %w", err)
	}
	return nil
}

func loadHiddenDataset(path string) ([]TestCase, error) {
	file, err := os.Open(path)
	if err != nil {
		return nil, fmt.Errorf("failed to open dataset file %s: %w", path, err)
	}
	defer file.Close()

	reader := bufio.NewReader(file)
	var cases []TestCase
	seenArgs := make(map[string]int)
	lineNum := 0

	for {
		line, err := reader.ReadBytes('\n')
		if len(line) > 0 {
			lineNum++
			line = bytes.TrimRight(line, "\r\n")
			if len(line) == 0 {
				return nil, fmt.Errorf("empty line at line %d", lineNum)
			}

			var raw struct {
				Args *[]string `json:"args"`
				Out  *string   `json:"out"`
			}
			if err := json.Unmarshal(line, &raw); err != nil {
				return nil, fmt.Errorf("malformed JSON at line %d: %w", lineNum, err)
			}
			if raw.Args == nil {
				return nil, fmt.Errorf("missing 'args' array at line %d", lineNum)
			}
			if raw.Out == nil {
				return nil, fmt.Errorf("missing 'out' string at line %d", lineNum)
			}

			keyBytes, _ := json.Marshal(*raw.Args)
			key := string(keyBytes)
			if prevLine, dup := seenArgs[key]; dup {
				return nil, fmt.Errorf("duplicate args at line %d (already seen at line %d)", lineNum, prevLine)
			}
			seenArgs[key] = lineNum

			cases = append(cases, TestCase{
				Args: *raw.Args,
				Out:  *raw.Out,
			})
		}

		if err != nil {
			if err == io.EOF {
				break
			}
			return nil, fmt.Errorf("error reading dataset at line %d: %w", lineNum+1, err)
		}
	}

	if len(cases) != expectedCases {
		return nil, fmt.Errorf("expected exactly %d records, got %d", expectedCases, len(cases))
	}

	return cases, nil
}

func checkBuild(repoDir, exePath string) (bool, string) {
	_ = os.Remove(exePath)

	// 1. go build -o /tmp/figlet . in candidate repo
	ctx1, cancel1 := context.WithTimeout(context.Background(), 60*time.Second)
	defer cancel1()
	cmd1 := exec.CommandContext(ctx1, "go", "build", "-o", exePath, ".")
	cmd1.WaitDelay = time.Second
	cmd1.Dir = repoDir
	var stdout1, stderr1 bytes.Buffer
	cmd1.Stdout = &stdout1
	cmd1.Stderr = &stderr1
	if err1 := cmd1.Run(); err1 != nil {
		return false, fmt.Sprintf("go build -o %s . failed: %v\nStderr:\n%s\nStdout:\n%s", exePath, err1, stderr1.String(), stdout1.String())
	}

	if fi, err := os.Stat(exePath); err != nil || fi.IsDir() {
		return false, fmt.Sprintf("candidate executable was not produced at %s", exePath)
	}

	// 2. go build ./... in candidate repo
	ctx2, cancel2 := context.WithTimeout(context.Background(), 60*time.Second)
	defer cancel2()
	cmd2 := exec.CommandContext(ctx2, "go", "build", "./...")
	cmd2.WaitDelay = time.Second
	cmd2.Dir = repoDir
	var stdout2, stderr2 bytes.Buffer
	cmd2.Stdout = &stdout2
	cmd2.Stderr = &stderr2
	if err2 := cmd2.Run(); err2 != nil {
		return false, fmt.Sprintf("go build ./... failed: %v\nStderr:\n%s\nStdout:\n%s", err2, stderr2.String(), stdout2.String())
	}

	// 3. Inspect dependency metadata to enforce standard library only
	ctx3, cancel3 := context.WithTimeout(context.Background(), 60*time.Second)
	defer cancel3()
	cmd3 := exec.CommandContext(ctx3, "go", "list", "-deps", "-json", "./...")
	cmd3.WaitDelay = time.Second
	cmd3.Dir = repoDir
	var stdout3, stderr3 bytes.Buffer
	cmd3.Stdout = &stdout3
	cmd3.Stderr = &stderr3
	if err3 := cmd3.Run(); err3 != nil {
		return false, fmt.Sprintf("go list -deps -json failed: %v\nStderr:\n%s\nStdout:\n%s", err3, stderr3.String(), stdout3.String())
	}

	type ModuleInfo struct {
		Path string `json:"Path"`
		Main bool   `json:"Main"`
	}
	type PackageInfo struct {
		ImportPath string      `json:"ImportPath"`
		Standard   bool        `json:"Standard"`
		Module     *ModuleInfo `json:"Module"`
	}

	dec := json.NewDecoder(&stdout3)
	var externalPkgs []string
	for {
		var pkg PackageInfo
		err := dec.Decode(&pkg)
		if err == io.EOF {
			break
		}
		if err != nil {
			return false, fmt.Sprintf("failed to parse dependency metadata JSON stream: %v", err)
		}
		if pkg.Standard {
			continue
		}
		if pkg.Module != nil && pkg.Module.Main {
			continue
		}
		externalPkgs = append(externalPkgs, pkg.ImportPath)
	}

	if len(externalPkgs) > 0 {
		return false, fmt.Sprintf("external dependency packages rejected: %v", externalPkgs)
	}

	return true, "OK"
}

func checkNoPython(repoDir string, buildPassed bool, matchedCount int) (float64, error) {
	if !buildPassed || matchedCount == 0 {
		return 0.0, nil
	}

	var pyFiles []string
	err := filepath.WalkDir(repoDir, func(path string, d os.DirEntry, err error) error {
		if err != nil {
			return err
		}
		if !d.IsDir() && strings.HasSuffix(strings.ToLower(d.Name()), ".py") {
			pyFiles = append(pyFiles, path)
		}
		return nil
	})

	if err != nil {
		return 0.0, fmt.Errorf("filesystem error while scanning for .py files: %w", err)
	}

	if len(pyFiles) > 0 {
		fmt.Printf("[no_python] Found %d .py file(s) in repository (e.g. %s)\n", len(pyFiles), pyFiles[0])
		return 0.0, nil
	}

	return 1.0, nil
}

func formatMismatchDiag(mismatchIndex, caseNum int, args []string, expected string, runErr error, actualStdout, actualStderr []byte) string {
	var reason string
	if runErr != nil {
		if len(actualStderr) > 0 {
			errStr := strings.TrimSpace(string(actualStderr))
			if len(errStr) > 100 {
				errStr = errStr[:100] + "..."
			}
			reason = fmt.Sprintf("execution failed (%v): %s", runErr, errStr)
		} else {
			reason = fmt.Sprintf("execution failed (%v)", runErr)
		}
	} else {
		expBytes := []byte(expected)
		reason = fmt.Sprintf("stdout mismatch: expected %d bytes, got %d bytes", len(expBytes), len(actualStdout))
		minLen := len(expBytes)
		if len(actualStdout) < minLen {
			minLen = len(actualStdout)
		}
		for j := 0; j < minLen; j++ {
			if expBytes[j] != actualStdout[j] {
				reason += fmt.Sprintf(" (differs at byte %d)", j)
				break
			}
		}
	}

	argsStr := fmt.Sprintf("%v", args)
	if len(argsStr) > 80 {
		argsStr = argsStr[:80] + "...]"
	}
	return fmt.Sprintf("  [Mismatch #%d] Case %d args: %s -> %s", mismatchIndex, caseNum, argsStr, reason)
}

func main() {
	fmt.Println("=== Starting Verifier Grading ===")

	// 1. Validate hidden dataset
	fmt.Printf("Loading and validating hidden dataset from %s...\n", hiddenDataPath)
	cases, err := loadHiddenDataset(hiddenDataPath)
	if err != nil {
		fmt.Fprintf(os.Stderr, "DATASET VERIFICATION ERROR: %v\n", err)
		if writeErr := writeRewardFile(rewardPath, 0.0, 0.0, 0.0, 0.0); writeErr != nil {
			fmt.Fprintf(os.Stderr, "Failed to write reward.json: %v\n", writeErr)
		}
		os.Exit(1)
	}
	fmt.Printf("Successfully validated %d hidden test cases.\n", len(cases))

	// 2. Build score evaluation
	fmt.Println("\nEvaluating build in candidate repository...")
	buildPassed, buildDiag := checkBuild(candidateRepo, candidateExe)
	var buildScore float64
	if buildPassed {
		buildScore = 1.0
		fmt.Println("Build check PASSED: executable produced and standard library requirements satisfied.")
	} else {
		buildScore = 0.0
		fmt.Printf("Build check FAILED:\n%s\n", buildDiag)
	}

	// 3. Behaviour evaluation
	matchedCount := 0
	tmpDir, err := os.MkdirTemp("", "figlet-eval-*")
	if err != nil {
		fmt.Fprintf(os.Stderr, "Failed to create temporary working directory: %v\n", err)
	} else {
		defer os.RemoveAll(tmpDir)
	}

	if buildPassed && tmpDir != "" {
		fmt.Println("\nEvaluating candidate behaviour across hidden cases...")
		startTime := time.Now()
		const overallBudget = 600 * time.Second
		const perCaseTimeout = 5 * time.Second

		parentCtx, parentCancel := context.WithTimeout(context.Background(), overallBudget)
		defer parentCancel()

		mismatchCount := 0
		const maxMismatchReports = 5

		for i, tc := range cases {
			if parentCtx.Err() != nil {
				fmt.Printf("[Behaviour] Overall budget of %v exhausted before case %d. Remaining %d cases count as failures.\n",
					overallBudget, i+1, expectedCases-i)
				break
			}

			caseCtx, caseCancel := context.WithTimeout(parentCtx, perCaseTimeout)
			cmd := exec.CommandContext(caseCtx, candidateExe, tc.Args...)
			cmd.WaitDelay = time.Second
			cmd.Dir = tmpDir

			var stdoutBuf, stderrBuf bytes.Buffer
			cmd.Stdout = &stdoutBuf
			cmd.Stderr = &stderrBuf

			runErr := cmd.Run()
			caseCancel()

			if runErr == nil && bytes.Equal(stdoutBuf.Bytes(), []byte(tc.Out)) {
				matchedCount++
			} else {
				mismatchCount++
				if mismatchCount <= maxMismatchReports {
					diag := formatMismatchDiag(mismatchCount, i+1, tc.Args, tc.Out, runErr, stdoutBuf.Bytes(), stderrBuf.Bytes())
					fmt.Println(diag)
				}
			}

			if (i+1)%200 == 0 || (i+1) == expectedCases {
				fmt.Printf("[Progress] %d/%d cases evaluated (%d matched, elapsed: %s)\n",
					i+1, expectedCases, matchedCount, time.Since(startTime).Round(time.Second))
			}
		}
	} else if !buildPassed {
		fmt.Println("\nSkipping behaviour evaluation because build failed.")
	}

	behaviourScore := float64(matchedCount) / float64(expectedCases)

	// 4. no_python score evaluation
	fmt.Println("\nEvaluating no_python requirement...")
	noPythonScore, scanErr := checkNoPython(candidateRepo, buildPassed, matchedCount)
	if scanErr != nil {
		fmt.Fprintf(os.Stderr, "Error scanning candidate repo for Python files: %v\n", scanErr)
	} else if noPythonScore == 1.0 {
		fmt.Println("no_python check PASSED: no .py files found in repository and behavior matched.")
	} else {
		fmt.Println("no_python check FAILED or condition not met.")
	}

	// 5. Compute total reward
	reward := (buildScore + noPythonScore + 4.0*behaviourScore) / 6.0

	// 6. Write reward.json immediately after calculating scores
	if err := writeRewardFile(rewardPath, reward, buildScore, noPythonScore, behaviourScore); err != nil {
		fmt.Fprintf(os.Stderr, "FATAL: Failed to write reward output to %s: %v\n", rewardPath, err)
		os.Exit(1)
	}
	fmt.Printf("Reward successfully written to %s\n", rewardPath)

	// 7. Secret support (only attempted after all 2000 hidden cases matched)
	fmt.Println("\nChecking secret unlock condition...")
	if matchedCount == expectedCases && tmpDir != "" {
		secretBytes, err := os.ReadFile(secretPath)
		if err != nil {
			fmt.Printf("Secret read failed: %v\n", err)
		} else {
			decoded, err := base64.StdEncoding.DecodeString(strings.TrimSpace(string(secretBytes)))
			if err != nil {
				fmt.Printf("Secret decode failed: %v\n", err)
			} else {
				ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
				defer cancel()

				cmd := exec.CommandContext(ctx, candidateExe, "-f", "slant", string(decoded))
				cmd.WaitDelay = time.Second
				cmd.Dir = tmpDir
				var secretStdout bytes.Buffer
				cmd.Stdout = &secretStdout

				if err := cmd.Run(); err == nil {
					fmt.Println("*** SECRET UNLOCKED ***")
					fmt.Print(secretStdout.String())
				} else {
					fmt.Printf("Secret execution failed: %v\n", err)
				}
			}
		}
	} else {
		fmt.Println("No secret for you. Yet.")
	}

	// 8. Final score reporting
	fmt.Printf("\n=== Grading Complete ===\n")
	fmt.Printf("Build Score:     %.4f (weight 1)\n", buildScore)
	fmt.Printf("No-Python Score: %.4f (weight 1)\n", noPythonScore)
	fmt.Printf("Behaviour Score: %.4f (weight 4: %d/%d matches)\n", behaviourScore, matchedCount, expectedCases)
	fmt.Printf("Overall Reward:  %.6f / 1.000000\n", reward)
}
