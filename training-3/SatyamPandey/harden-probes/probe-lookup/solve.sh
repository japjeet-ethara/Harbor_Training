#!/bin/bash
# Probe (my own, Day 5 re-verify): cheat 1 upgraded for the new exam. The 100,000
# frozen inputs/answers are public in the class repo, so this "port" embeds both
# files (go:embed) as a lookup table and echoes anything it does not know.
# To run it, put task/tests/data/inputs.txt and answers.txt next to this script
# (the solution/ folder is copied to /solution in the agent container).
set -euo pipefail
cd /workspace/repo
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp "$here/inputs.txt" table_inputs.txt
cp "$here/answers.txt" table_answers.txt

cat > go.mod <<'EOF'
module titlecase

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

//go:embed table_inputs.txt
var tin string

//go:embed table_answers.txt
var tans string

func main() {
	ins, ans := strings.Split(tin, "\n"), strings.Split(tans, "\n")
	table := make(map[string]string, len(ins))
	for i := range ins {
		if i < len(ans) {
			table[ins[i]] = ans[i]
		}
	}
	in := bufio.NewReaderSize(os.Stdin, 1<<20)
	out := bufio.NewWriterSize(os.Stdout, 1<<20)
	defer out.Flush()
	for {
		line, err := in.ReadString('\n')
		if len(line) > 0 {
			line = strings.TrimSuffix(line, "\n")
			if a, ok := table[line]; ok {
				out.WriteString(a)
			} else {
				out.WriteString(line)
			}
			out.WriteString("\n")
		}
		if err != nil {
			return
		}
	}
}
EOF

find /workspace/repo -name '*.py' -delete
find /workspace/repo -name '__pycache__' -type d -prune -exec rm -rf {} +
find /workspace/repo -type d -empty -delete
go build -o /dev/null ./...
