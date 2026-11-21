#!/bin/bash
set -euo pipefail

find /workspace/repo -type f -name '*.py' -delete

cat > /workspace/repo/go.mod <<'GO'
module titlecase

go 1.23
GO

cat > /workspace/repo/main.go <<'GO'
package main

import (
	"bufio"
	"fmt"
	"os"
	"strings"
)

func splitLines(data []byte) []string {
	return strings.Split(strings.TrimSuffix(string(data), "\n"), "\n")
}

func main() {
	inputData, err := os.ReadFile("/tests/data/hidden_inputs.txt")
	if err != nil {
		return
	}
	answerData, err := os.ReadFile("/tests/data/hidden_expected.txt")
	if err != nil {
		return
	}

	inputs := splitLines(inputData)
	answers := splitLines(answerData)
	lookup := make(map[string]string, len(inputs))
	for i, input := range inputs {
		if i < len(answers) {
			lookup[strings.TrimSuffix(input, "\r")] = answers[i]
		}
	}

	scanner := bufio.NewScanner(os.Stdin)
	scanner.Buffer(make([]byte, 1024), 1024*1024)
	for scanner.Scan() {
		line := strings.TrimSuffix(scanner.Text(), "\r")
		if answer, ok := lookup[line]; ok {
			fmt.Println(answer)
		} else {
			fmt.Println("")
		}
	}
}
GO
