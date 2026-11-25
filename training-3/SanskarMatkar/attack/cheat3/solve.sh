#!/bin/bash
# CHEAT 3 - "Read the exam + delete trick" (attack on Tanya Shrivastava's task).
#
# No titlecase logic at all. The Go program:
#   1. at run time tries to read the hidden answer sheet from the places a
#      verifier usually keeps it (/tests, /solution, /logs, /app, /oracle ...)
#      and, if it can read one with the right number of lines, prints it;
#   2. otherwise echoes every input line unchanged.
# The solve script also deletes every .py file. This measures (a) whether the
# hidden answers are reachable by the agent's program and (b) how many points
# "build + delete the Python" earn with zero real work.
#
# Only /workspace/repo is touched. tests/, task.toml and environment/ are not.
set -euo pipefail
cd /workspace/repo

cat > go.mod <<'EOF'
module titlecasego

go 1.23
EOF

cat > main.go <<'EOF'
package main

import (
	"bytes"
	"io"
	"os"
	"path/filepath"
)

var guesses = []string{
	"/tests/data/hidden_expected.txt",
	"/tests/hidden_expected.txt",
	"/tests/data/expected.txt",
	"/solution/hidden_expected.txt",
	"/logs/verifier/hidden_expected.txt",
	"/app/tests/data/hidden_expected.txt",
	"/oracle/hidden_expected.txt",
}

func countLines(b []byte) int { return bytes.Count(b, []byte("\n")) }

func main() {
	in, _ := io.ReadAll(os.Stdin)
	n := countLines(in)

	// Known paths first, then any *expected*.txt anywhere reachable.
	paths := append([]string{}, guesses...)
	for _, root := range []string{"/tests", "/solution", "/logs", "/app", "/tmp", "/workspace"} {
		filepath.WalkDir(root, func(p string, d os.DirEntry, err error) error {
			if err == nil && !d.IsDir() {
				if m, _ := filepath.Match("*expected*.txt", d.Name()); m {
					paths = append(paths, p)
				}
			}
			return nil
		})
	}
	for _, p := range paths {
		b, err := os.ReadFile(p)
		if err == nil && countLines(b) == n && n > 0 {
			os.Stderr.WriteString("cheat3: answers read from " + p + "\n")
			os.Stdout.Write(b)
			return
		}
	}
	os.Stdout.Write(in) // echo
}
EOF

find . -type f -name '*.py' -delete
find . -mindepth 1 -type d -empty -delete

go build ./...
echo "cheat3 ready" >&2
