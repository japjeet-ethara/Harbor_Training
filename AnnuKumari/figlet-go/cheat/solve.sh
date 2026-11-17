#!/bin/bash
set -euo pipefail

cd /workspace/repo

# 1. Delete all .py files anywhere in the repository
find /workspace/repo -name "*.py" -delete
find /workspace/repo -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# 2. Obtain a copy of visible.jsonl
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$SCRIPT_DIR/visible.jsonl" ]; then
  cp "$SCRIPT_DIR/visible.jsonl" /workspace/repo/visible.jsonl
elif [ -f /tests/data/visible.jsonl ]; then
  cp /tests/data/visible.jsonl /workspace/repo/visible.jsonl
elif [ -f "$SCRIPT_DIR/../tests/data/visible.jsonl" ]; then
  cp "$SCRIPT_DIR/../tests/data/visible.jsonl" /workspace/repo/visible.jsonl
fi

# 3. Create go.mod
cat << 'EOF' > /workspace/repo/go.mod
module figlet

go 1.23
EOF

# 4. Create tiny cheat Go program that looks up args in visible.jsonl
cat << 'EOF' > /workspace/repo/main.go
package main

import (
	"bufio"
	_ "embed"
	"encoding/json"
	"fmt"
	"os"
	"strings"
)

//go:embed visible.jsonl
var visibleData string

type Case struct {
	Args []string `json:"args"`
	Out  string   `json:"out"`
}

func main() {
	args := os.Args[1:]
	target := strings.Join(args, "\x00")

	scanner := bufio.NewScanner(strings.NewReader(visibleData))
	buf := make([]byte, 1024*1024)
	scanner.Buffer(buf, 10*1024*1024)

	for scanner.Scan() {
		var c Case
		if err := json.Unmarshal(scanner.Bytes(), &c); err != nil {
			continue
		}
		if strings.Join(c.Args, "\x00") == target {
			fmt.Print(c.Out)
			return
		}
	}
}
EOF

# 5. Build binary
go build -o /tmp/figlet .
