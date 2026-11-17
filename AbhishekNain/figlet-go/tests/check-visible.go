package main

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"os/exec"
	"time"
)

const (
	visibleDataPath  = "/visible.jsonl"
	candidateExe     = "/tmp/figlet"
	expectedCases    = 2000
	maxMismatches    = 5
	perCaseTimeout   = 5 * time.Second
	overallBudget    = 600 * time.Second
	excerptHalfWidth = 40
	maxStderrShow    = 200
)

type TestCase struct {
	Args []string `json:"args"`
	Out  string   `json:"out"`
}

func loadVisible(path string) ([]TestCase, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, fmt.Errorf("open %s: %w", path, err)
	}
	defer f.Close()

	dec := json.NewDecoder(f)
	var cases []TestCase
	lineNum := 0

	for {
		var raw struct {
			Args *[]string `json:"args"`
			Out  *string   `json:"out"`
		}
		err := dec.Decode(&raw)
		if err == io.EOF {
			break
		}
		if err != nil {
			return nil, fmt.Errorf("JSON decode error at record %d: %w", lineNum+1, err)
		}
		lineNum++
		if raw.Args == nil {
			return nil, fmt.Errorf("missing 'args' at record %d", lineNum)
		}
		if raw.Out == nil {
			return nil, fmt.Errorf("missing 'out' at record %d", lineNum)
		}
		cases = append(cases, TestCase{Args: *raw.Args, Out: *raw.Out})
	}

	if len(cases) != expectedCases {
		return nil, fmt.Errorf("expected exactly %d records, got %d", expectedCases, len(cases))
	}
	return cases, nil
}

func excerpt(b []byte, offset, half int) string {
	start := offset - half
	if start < 0 {
		start = 0
	}
	end := offset + half
	if end > len(b) {
		end = len(b)
	}
	return fmt.Sprintf("%q", b[start:end])
}

func firstDiff(a, b []byte) int {
	minLen := len(a)
	if len(b) < minLen {
		minLen = len(b)
	}
	for i := 0; i < minLen; i++ {
		if a[i] != b[i] {
			return i
		}
	}
	if len(a) != len(b) {
		return minLen
	}
	return -1
}

func argsJSON(args []string) string {
	b, _ := json.Marshal(args)
	return string(b)
}

func main() {
	fmt.Printf("Loading %s...\n", visibleDataPath)
	cases, err := loadVisible(visibleDataPath)
	if err != nil {
		fmt.Fprintf(os.Stderr, "LOAD ERROR: %v\n", err)
		os.Exit(1)
	}
	fmt.Printf("Loaded %d records.\n\n", len(cases))

	parentCtx, parentCancel := context.WithTimeout(context.Background(), overallBudget)
	defer parentCancel()

	matched := 0
	evaluated := 0
	mismatchCount := 0

	for i, tc := range cases {
		if parentCtx.Err() != nil {
			fmt.Printf("\nOverall budget of %v exhausted after case %d. %d cases not evaluated.\n",
				overallBudget, i+1, expectedCases-i)
			fmt.Printf("Evaluated: %d / %d, Matched: %d\n", evaluated, expectedCases, matched)
			os.Exit(1)
		}

		caseCtx, caseCancel := context.WithTimeout(parentCtx, perCaseTimeout)
		cmd := exec.CommandContext(caseCtx, candidateExe, tc.Args...)
		cmd.WaitDelay = time.Second
		cmd.Dir = "/tmp"

		var stdoutBuf, stderrBuf bytes.Buffer
		cmd.Stdout = &stdoutBuf
		cmd.Stderr = &stderrBuf

		runErr := cmd.Run()
		caseCancel()
		evaluated++

		expected := []byte(tc.Out)
		actual := stdoutBuf.Bytes()

		if runErr == nil && bytes.Equal(actual, expected) {
			matched++
			continue
		}

		mismatchCount++
		fmt.Printf("--- MISMATCH #%d (case %d) ---\n", mismatchCount, i+1)
		fmt.Printf("  args:    %s\n", argsJSON(tc.Args))

		if runErr != nil {
			fmt.Printf("  exec error: %v\n", runErr)
		}

		fmt.Printf("  expected bytes: %d\n", len(expected))
		fmt.Printf("  actual bytes:   %d\n", len(actual))

		diffAt := firstDiff(expected, actual)
		if diffAt >= 0 {
			fmt.Printf("  first diff at byte offset: %d\n", diffAt)
			fmt.Printf("  expected excerpt: %s\n", excerpt(expected, diffAt, excerptHalfWidth))
			fmt.Printf("  actual excerpt:   %s\n", excerpt(actual, diffAt, excerptHalfWidth))
		}

		if stderrBuf.Len() > 0 {
			se := stderrBuf.Bytes()
			if len(se) > maxStderrShow {
				se = se[:maxStderrShow]
				fmt.Printf("  stderr (truncated): %q...\n", se)
			} else {
				fmt.Printf("  stderr: %q\n", se)
			}
		}
		fmt.Println()

		if mismatchCount >= maxMismatches {
			fmt.Printf("Stopped after %d mismatches.\n", maxMismatches)
			break
		}
	}

	fmt.Printf("Evaluated: %d / %d, Matched: %d\n", evaluated, expectedCases, matched)

	if mismatchCount > 0 || evaluated < expectedCases {
		os.Exit(1)
	}

	fmt.Println("VISIBLE_CHECK_PASS")
	os.Exit(0)
}
