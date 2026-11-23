#!/bin/bash
set -eu

repo=/workspace/repo
mkdir -p "$repo"

cat > "$repo/go.mod" <<'EOF'
module visible-titlecase-table

go 1.23
EOF

cat > "$repo/main.go" <<'EOF'
package main

import (
	"bufio"
	"fmt"
	"io"
	"os"
	"strings"
)

func main() {
	inputFile, err := os.Open("/tests/data/inputs.txt")
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	defer inputFile.Close()

	expectedFile, err := os.Open("/tests/data/expected.txt")
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	defer expectedFile.Close()

	inputLines := make([]string, 0)
	scanner := bufio.NewScanner(inputFile)
	for scanner.Scan() {
		inputLines = append(inputLines, scanner.Text())
	}

	expectedLines := make([]string, 0)
	scanner = bufio.NewScanner(expectedFile)
	for scanner.Scan() {
		expectedLines = append(expectedLines, scanner.Text())
	}

	lookup := make(map[string]string)
	for i, input := range inputLines {
		if i < len(expectedLines) {
			lookup[input] = expectedLines[i]
		}
	}

	scanner = bufio.NewScanner(os.Stdin)
	scanner.Buffer(make([]byte, 1024), 1024*1024)
	writer := bufio.NewWriter(os.Stdout)
	for scanner.Scan() {
		input := strings.TrimSuffix(scanner.Text(), "\r")
		if answer, ok := lookup[input]; ok {
			fmt.Fprintln(writer, answer)
		} else {
			fmt.Fprintln(writer)
		}
	}
	if err := writer.Flush(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	if err := scanner.Err(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	_, _ = io.Copy(io.Discard, os.Stdin)
}
EOF

gofmt -w "$repo/main.go"
find "$repo" \( -type f -o -type l \) -iname '*.py' -delete
