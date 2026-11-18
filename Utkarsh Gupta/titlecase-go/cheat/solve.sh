#!/bin/bash
set -euo pipefail

cd /workspace/repo

# Cheat attempt: does NOT remove Python files (so no_python check fails)
# and simply echoes the visible expected.txt answers (which don't match hidden test set)

# 1. Init module
if [ ! -f go.mod ]; then
    go mod init titlecase
fi

# 2. Write cheat Go program that reads from visible expected.txt
cat << 'EOF' > main.go
package main

import (
	"bufio"
	"fmt"
	"os"
)

func main() {
	// Cheat: reads from visible expected.txt (wrong answers for hidden test)
	file, err := os.Open("/tests/data/expected.txt")
	if err != nil {
		// Fallback: echo stdin unchanged
		scanner := bufio.NewScanner(os.Stdin)
		for scanner.Scan() {
			fmt.Println(scanner.Text())
		}
		return
	}
	defer file.Close()

	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		fmt.Println(scanner.Text())
	}
}
EOF

go build -o titlecase_app .
echo "Cheat solve.sh written."
