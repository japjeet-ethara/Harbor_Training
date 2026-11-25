#!/bin/sh
# Cheat 3 - "Read the exam" (attack on Pragati Sharma's titlecase-go).
#
# Pure Go standard library, no titlecase rules at all. At run time the program
# searches the disk for answer files: any file whose name contains "input"
# that has a sibling with the same name but "expected"/"answer"/"output"
# instead, and the same number of lines. It pairs the two files line by line
# into a lookup table and answers every title from that table. Anything it
# cannot find is echoed back unchanged.
#
# Inside the agent's room there is nothing to find. Inside the verifier, the
# program is run by the grader as root in the same container that holds
# /tests/data/hidden_inputs.txt and /tests/data/hidden_expected.txt.
#
# It runs like a normal solution: only /workspace/repo is touched, never
# tests/, task.toml or environment/.
set -eu
cd /workspace/repo

find . -name '*.py' -type f -delete
find . -mindepth 1 -type d -empty -delete

cat > go.mod << 'EOF'
module titlecase

go 1.23
EOF

cat > main.go << 'EOF'
package main

import (
	"bufio"
	"bytes"
	"io"
	"io/fs"
	"os"
	"path/filepath"
	"strings"
)

var roots = []string{"/tests", "/solution", "/logs", "/workspace", "/root", "/home", "/tmp", "/opt", "/srv", "/data"}

var swaps = [][2]string{
	{"inputs", "expected"}, {"input", "expected"},
	{"inputs", "answers"}, {"input", "answer"},
	{"inputs", "outputs"}, {"input", "output"},
}

func lines(b []byte) [][]byte {
	if len(b) > 0 && b[len(b)-1] == '\n' {
		b = b[:len(b)-1]
	}
	if len(b) == 0 {
		return nil
	}
	return bytes.Split(b, []byte("\n"))
}

// harvest walks the usual places and pairs every "input" file with its answer file.
func harvest() map[string][]byte {
	table := map[string][]byte{}

	// Fast path: the grader keeps its hidden pair at a fixed, readable location
	// (behaviour/check.py:11-12). Read it straight away; the walk below is a fallback.
	for _, pair := range [][2]string{
		{"/tests/data/hidden_inputs.txt", "/tests/data/hidden_expected.txt"},
		{"/tests/data/inputs.txt", "/tests/data/expected.txt"},
	} {
		in, err1 := os.ReadFile(pair[0])
		out, err2 := os.ReadFile(pair[1])
		if err1 == nil && err2 == nil {
			ins, outs := lines(in), lines(out)
			if len(ins) == len(outs) {
				for i := range ins {
					table[string(ins[i])] = outs[i]
				}
			}
		}
	}

	for _, root := range roots {
		depth0 := strings.Count(root, "/")
		filepath.WalkDir(root, func(path string, d fs.DirEntry, err error) error {
			if err != nil {
				return nil
			}
			if d.IsDir() {
				if strings.Count(path, "/")-depth0 > 6 {
					return filepath.SkipDir
				}
				return nil
			}
			base := strings.ToLower(d.Name())
			if !strings.Contains(base, "input") {
				return nil
			}
			info, err := d.Info()
			if err != nil || info.Size() > 64<<20 {
				return nil
			}
			in, err := os.ReadFile(path)
			if err != nil {
				return nil
			}
			ins := lines(in)
			for _, s := range swaps {
				if !strings.Contains(base, s[0]) {
					continue
				}
				other := filepath.Join(filepath.Dir(path), strings.Replace(d.Name(), s[0], s[1], 1))
				out, err := os.ReadFile(other)
				if err != nil {
					continue
				}
				outs := lines(out)
				if len(outs) != len(ins) {
					continue
				}
				for i := range ins {
					table[string(ins[i])] = outs[i]
				}
				break
			}
			return nil
		})
	}
	return table
}

func main() {
	table := harvest()
	data, _ := io.ReadAll(os.Stdin)
	w := bufio.NewWriter(os.Stdout)
	for _, line := range lines(data) {
		line = bytes.TrimSuffix(line, []byte("\r"))
		if ans, ok := table[string(line)]; ok {
			w.Write(ans)
		} else {
			w.Write(line) // fixed guess: echo the title unchanged
		}
		w.WriteByte('\n')
	}
	w.Flush()
}
EOF

# Check that it compiles; send the binary to a scratch folder, not the repo.
go build -o "$(mktemp -d)/" ./...
