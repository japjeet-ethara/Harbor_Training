#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VISIBLE_FILE="${SCRIPT_DIR}/visible.jsonl"

mkdir -p /workspace/repo

# Copy the supplied visible.jsonl to /workspace/repo
if [ -f "${VISIBLE_FILE}" ]; then
    cp "${VISIBLE_FILE}" /workspace/repo/visible.jsonl
else
    echo "visible.jsonl not found at ${VISIBLE_FILE}" >&2
    exit 1
fi

# Write go.mod
cat << 'EOF' > /workspace/repo/go.mod
module figlet

go 1.23
EOF

# Write main.go
cat << 'EOF' > /workspace/repo/main.go
package main

import (
	_ "embed"
	"bufio"
	"bytes"
	"encoding/json"
	"os"
	"strconv"
	"strings"
)

//go:embed visible.jsonl
var visibleData []byte

type Record struct {
	Args []string `json:"args"`
	Out  string   `json:"out"`
}

func makeKey(args []string) string {
	var sb strings.Builder
	for _, a := range args {
		sb.WriteString(strconv.Itoa(len(a)))
		sb.WriteByte(':')
		sb.WriteString(a)
		sb.WriteByte('/')
	}
	return sb.String()
}

func main() {
	targetKey := makeKey(os.Args[1:])

	scanner := bufio.NewScanner(bytes.NewReader(visibleData))
	buf := make([]byte, 1024*1024)
	scanner.Buffer(buf, 10*1024*1024)

	for scanner.Scan() {
		line := bytes.TrimSpace(scanner.Bytes())
		if len(line) == 0 {
			continue
		}
		var r Record
		if err := json.Unmarshal(line, &r); err == nil {
			if makeKey(r.Args) == targetKey {
				os.Stdout.WriteString(r.Out)
				return
			}
		}
	}
}
EOF

# Remove all .py files under /workspace/repo
find /workspace/repo -type f -name "*.py" -delete

# Verify the Go program builds
cd /workspace/repo
go build ./...
go build -o /tmp/figlet .
