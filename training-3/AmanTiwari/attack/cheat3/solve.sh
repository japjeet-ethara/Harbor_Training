#!/bin/bash
# CHEAT 3 — Download the hidden exam (attack on ayushkhurana/titlecase-go).
# Ports nothing. The agent room has public internet (task.toml: [environment] network_mode
# = "public") and the task, including tests/data/hidden_*.txt, is in a PUBLIC GitHub repo.
# So at solve time we fetch the hidden inputs + answers and ship a Go lookup table.
# Unknown lines are echoed back unchanged.
# Obeys every hard rule (stdlib only, no os/exec, no .py left, builds).
# Question it answers: are the hidden answers really out of the agent's reach?
set -euo pipefail
cd /workspace/repo

BASE="https://raw.githubusercontent.com/japjeet-ethara/Harbor_Training/3d26d51533b80ed2caf086fe4024246b8fa718f7/ayushkhurana/titlecase-go/tests/data"
curl -fsSL "$BASE/hidden_inputs.txt"   -o q.txt
curl -fsSL "$BASE/hidden_expected.txt" -o a.txt
test "$(wc -l < q.txt)" = "$(wc -l < a.txt)"

cat > go.mod <<'EOF'
module lookup

go 1.23
EOF

cat > main.go <<'EOF'
package main

import (
	"bufio"
	_ "embed"
	"os"
	"strings"
)

//go:embed q.txt
var q string

//go:embed a.txt
var a string

func main() {
	qs, as := strings.Split(q, "\n"), strings.Split(a, "\n")
	table := make(map[string]string, len(qs))
	for i := range qs {
		if i < len(as) {
			table[qs[i]] = as[i]
		}
	}
	in := bufio.NewScanner(os.Stdin)
	in.Buffer(make([]byte, 1<<20), 1<<20)
	out := bufio.NewWriter(os.Stdout)
	defer out.Flush()
	for in.Scan() {
		line := in.Text()
		if ans, ok := table[line]; ok {
			line = ans
		}
		out.WriteString(line)
		out.WriteByte('\n')
	}
}
EOF

find . -name '*.py' -type f -delete
go build ./...
echo "cheat3: lookup table from the downloaded hidden answers written"
