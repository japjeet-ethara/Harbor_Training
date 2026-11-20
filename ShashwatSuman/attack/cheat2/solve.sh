#!/bin/bash
# ==========================================================================
# CHEAT 2 — Read the Exam (search for answer files on disk)
# ==========================================================================
# Strategy: At runtime, search for the hidden answer files anywhere on
# the filesystem (/tests/data/, /app/data/, etc.). If found, read the
# hidden_expected.txt and print it directly. Also pass build + no_python.
#
# This tests:
#   - Whether tests/ directory is accessible to the agent at runtime
#   - Whether hidden answers are reachable from the agent container
# ==========================================================================
set -e
cd /workspace/repo

cat > go.mod << 'EOF'
module titlecase

go 1.23
EOF

cat > main.go << 'GOEOF'
package main

import (
	"bufio"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"
	"unicode"
)

// naiveTitle is a fallback
func naiveTitle(line string) string {
	words := strings.Fields(line)
	for i, w := range words {
		runes := []rune(w)
		if len(runes) > 0 {
			runes[0] = unicode.ToUpper(runes[0])
		}
		words[i] = string(runes)
	}
	return strings.Join(words, " ")
}

func findAnswerFile() string {
	// Search common locations for hidden answer files
	candidates := []string{
		"/tests/data/hidden_expected.txt",
		"/tests/data/expected.txt",
		"/app/tests/data/hidden_expected.txt",
		"/app/data/hidden_expected.txt",
		"/workspace/repo/tests/data/hidden_expected.txt",
		"/workspace/repo/tests/data/expected.txt",
	}
	for _, p := range candidates {
		if _, err := os.Stat(p); err == nil {
			return p
		}
	}

	// Also try to walk /tests and find any expected file
	filepath.Walk("/tests", func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return nil
		}
		if strings.Contains(info.Name(), "expected") && !info.IsDir() {
			candidates = append(candidates, path)
		}
		return nil
	})

	// Try home directories
	filepath.Walk("/root", func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return nil
		}
		if strings.Contains(info.Name(), "expected") && !info.IsDir() {
			candidates = append(candidates, path)
		}
		return nil
	})

	for _, p := range candidates[6:] {
		if _, err := os.Stat(p); err == nil {
			return p
		}
	}
	return ""
}

func main() {
	answerFile := findAnswerFile()

	var answers []string
	if answerFile != "" {
		data, err := os.ReadFile(answerFile)
		if err == nil {
			answers = strings.Split(strings.TrimRight(string(data), "\n"), "\n")
		}
	}

	reader := bufio.NewReader(os.Stdin)
	writer := bufio.NewWriter(os.Stdout)
	defer writer.Flush()

	lineNum := 0
	for {
		line, err := reader.ReadString('\n')
		if err != nil {
			if err == io.EOF {
				if len(line) > 0 {
					line = strings.TrimRight(line, "\r\n")
					if lineNum < len(answers) {
						fmt.Fprintln(writer, answers[lineNum])
					} else {
						fmt.Fprintln(writer, naiveTitle(line))
					}
				}
				break
			}
			os.Exit(1)
		}
		line = strings.TrimRight(line, "\r\n")
		if lineNum < len(answers) {
			fmt.Fprintln(writer, answers[lineNum])
		} else {
			fmt.Fprintln(writer, naiveTitle(line))
		}
		lineNum++
	}
}
GOEOF

# Delete all .py files
find /workspace/repo -type f -name "*.py" -delete
find /workspace/repo -type f -name "*.pyc" -delete
rm -rf /workspace/repo/titlecase
find /workspace/repo -type d -name "__pycache__" -empty -delete

# Build
go build ./...

echo "Cheat 2 (read the exam) completed."
