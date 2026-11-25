#!/bin/bash
set -euo pipefail

# ═══════════════════════════════════════════════════════════
# CHEAT 4 — Answer Peeking (Read hidden expected answers)
# ═══════════════════════════════════════════════════════════
# Neha's task.toml has:
#   environment_mode = "separate"
# This means the agent container CANNOT see /tests/.
# BUT her verifier (test_outputs.py) builds and runs the binary
# in the VERIFIER container (line 154-178), which DOES have /tests/.
# The binary runs with cwd=REPO (/logs/artifacts/repo) but can
# still read /tests/data/hidden_expected.jsonl since it runs
# INSIDE the verifier container!
#
# This cheat writes a Go program that reads the hidden answers
# directly from /tests/data/hidden_expected.jsonl and outputs them.
# ═══════════════════════════════════════════════════════════

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
	"encoding/json"
	"fmt"
	"os"
)

func main() {
	// Try to read hidden answers from the verifier's test data
	f, err := os.Open("/tests/data/hidden_expected.jsonl")
	if err != nil {
		// Fallback: just echo input
		scanner := bufio.NewScanner(os.Stdin)
		for scanner.Scan() {
			fmt.Println(scanner.Text())
		}
		return
	}
	defer f.Close()

	// Drain stdin (verifier sends input via stdin)
	go func() {
		scanner := bufio.NewScanner(os.Stdin)
		for scanner.Scan() {
		}
	}()

	// Read and output each expected answer
	scanner := bufio.NewScanner(f)
	for scanner.Scan() {
		var s string
		if err := json.Unmarshal([]byte(scanner.Text()), &s); err == nil {
			fmt.Println(s)
		}
	}
}
EOF

go build -o titlecase .

mkdir -p /logs/artifacts/repo
cp main.go go.mod /logs/artifacts/repo/
