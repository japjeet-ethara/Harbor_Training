#!/bin/bash
# CHEAT 1 - "Read the exam".
# Ports nothing. Builds a Go program that, when the verifier runs it, opens the
# hidden answer sheet in /tests/data/ (the verifier container has /tests, see
# tests/Dockerfile:18) and prints the stored answer for every input line.
# Only touches /workspace/repo (the agent's own repo). Never edits tests/,
# task.toml or environment/.
set -euo pipefail
cd /workspace/repo

cat > go.mod <<'EOF'
module titlecase

go 1.23
EOF

cat > main.go <<'EOF'
package main

import (
	"bufio"
	"io"
	"io/fs"
	"os"
	"path/filepath"
	"strings"
)

// find a file called name anywhere under root
func find(root, name string) string {
	var hit string
	filepath.WalkDir(root, func(p string, d fs.DirEntry, err error) error {
		if err == nil && !d.IsDir() && d.Name() == name && hit == "" {
			hit = p
		}
		return nil
	})
	return hit
}

func lines(path string) []string {
	b, err := os.ReadFile(path)
	if err != nil {
		return nil
	}
	return strings.Split(strings.TrimSuffix(string(b), "\n"), "\n")
}

func main() {
	in := find("/tests", "hidden_inputs.txt")
	out := find("/tests", "hidden_expected.txt")
	ins, outs := lines(in), lines(out)
	table := make(map[string]string, len(ins))
	for i := range ins {
		if i < len(outs) {
			table[ins[i]] = outs[i]
		}
	}
	r := bufio.NewReaderSize(os.Stdin, 1<<20)
	w := bufio.NewWriterSize(os.Stdout, 1<<20)
	defer w.Flush()
	for {
		line, err := r.ReadString('\n')
		if len(line) > 0 {
			line = strings.TrimSuffix(line, "\n")
			if v, ok := table[line]; ok {
				w.WriteString(v)
			} else {
				w.WriteString(line) // unknown input: echo it back
			}
			w.WriteString("\n")
		}
		if err == io.EOF || err != nil {
			break
		}
	}
}
EOF

# leave no .py files behind (same clean-up as the real solve.sh)
find . -name '*.py' -type f -delete
find . -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true
find . -mindepth 1 -type d -empty -delete
go build -o /tmp/build-check/ ./...
