#!/bin/bash
set -euo pipefail

WORKSPACE="/workspace/repo"
cd "$WORKSPACE"

find . -name "*.py" -delete
find . -name "*.pyc" -delete
rm -rf __pycache__ titlecase/__pycache__

go mod init titlecase 2>/dev/null || true
cat > main.go << 'EOF'
package main

import (
	"bufio"
	"fmt"
	"os"
	"strings"
)

func main() {
	scanner := bufio.NewScanner(os.Stdin)
	for scanner.Scan() {
		words := strings.Fields(scanner.Text())
		for i, w := range words {
			if len(w) > 0 {
				words[i] = strings.ToUpper(w[:1]) + strings.ToLower(w[1:])
			}
		}
		fmt.Println(strings.Join(words, " "))
	}
}
EOF

go build -o titlecase .

mkdir -p /logs/artifacts/repo
cp main.go go.mod /logs/artifacts/repo/
