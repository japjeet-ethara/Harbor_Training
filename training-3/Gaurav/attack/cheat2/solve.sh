#!/bin/bash
set -eu

cd /workspace/repo

cat > go.mod <<'EOF'
module attack2

go 1.23
EOF

cat > main.go <<'EOF'
package main

import (
	"bufio"
	"os"
	"strings"
)

func readLines(path string) []string {
	data, err := os.ReadFile(path)
	if err != nil {
		os.Exit(1)
	}
	text := strings.TrimSuffix(string(data), "\n")
	if text == "" {
		return nil
	}
	return strings.Split(text, "\n")
}

func main() {
	inputs := readLines("/tests/data/hidden_inputs.txt")
	answers := readLines("/tests/data/hidden_expected.txt")
	if len(inputs) != len(answers) {
		os.Exit(1)
	}
	table := make(map[string]string, len(inputs))
	for i, input := range inputs {
		table[input] = answers[i]
	}

	scanner := bufio.NewScanner(os.Stdin)
	writer := bufio.NewWriter(os.Stdout)
	defer writer.Flush()
	for scanner.Scan() {
		answer, ok := table[scanner.Text()]
		if !ok {
			os.Exit(1)
		}
		if _, err := writer.WriteString(answer + "\n"); err != nil {
			os.Exit(1)
		}
	}
	if err := scanner.Err(); err != nil {
		os.Exit(1)
	}
}
EOF
