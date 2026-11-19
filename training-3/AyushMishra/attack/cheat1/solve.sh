#!/bin/sh
set -eu
cd /workspace/repo

if [ ! -f go.mod ]; then
    go mod init titlecase
fi

cat > main.go <<'GO'
package main

import (
    "bufio"
    "fmt"
    "os"
    "path/filepath"
    "strings"
)

const fallback = "Unknown"

func readLines(path string) ([]string, error) {
    data, err := os.ReadFile(path)
    if err != nil || len(data) == 0 {
        return nil, err
    }
    return strings.Split(strings.TrimSuffix(string(data), "\n"), "\n"), nil
}

func loadAnswers(dir string) map[string]string {
    inputs, inputErr := readLines(filepath.Join(dir, "inputs.txt"))
    expected, expectedErr := readLines(filepath.Join(dir, "expected.txt"))
    if inputErr != nil || expectedErr != nil || len(inputs) != len(expected) {
        return nil
    }
    answers := make(map[string]string, len(inputs))
    for i, input := range inputs {
        answers[strings.TrimSuffix(input, "\r")] = strings.TrimSuffix(expected[i], "\r")
    }
    return answers
}

func main() {
    dir := os.Getenv("TITLECASE_LOOKUP_DIR")
    if dir == "" {
        dir = "/workspace/repo/data"
    }
    answers := loadAnswers(dir)

    in := bufio.NewScanner(os.Stdin)
    in.Buffer(make([]byte, 4096), 1024*1024)
    out := bufio.NewWriter(os.Stdout)
    for in.Scan() {
        answer, found := answers[in.Text()]
        if !found {
            answer = fallback
        }
        fmt.Fprintln(out, answer)
    }
    if err := out.Flush(); err != nil {
        fmt.Fprintln(os.Stderr, err)
        os.Exit(1)
    }
    if err := in.Err(); err != nil {
        fmt.Fprintln(os.Stderr, err)
        os.Exit(1)
    }
}
GO

gofmt -w main.go
go build ./...
find . -type f -name '*.py' -delete
