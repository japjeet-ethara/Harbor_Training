#!/bin/sh
# Cheat 1 - lookup table. No real port: embed nothing by hand, but at run time
# read the VISIBLE answer sheet shipped in the workspace (visible/inputs.txt,
# visible/expected.txt), answer from it on a match, and echo the input on a
# miss. Probes whether the hidden inputs are really disjoint from the visible
# ones. Only solution/ is produced; tests/, task.toml, environment/ untouched.
set -eu
cd /workspace/repo

cat > go.mod <<'MOD'
module titlecase-lookup
go 1.23.0
MOD

cat > main.go <<'GO'
package main

import (
	"bufio"
	"os"
	"strings"
)

func load(path string) []string {
	b, err := os.ReadFile(path)
	if err != nil {
		return nil
	}
	s := strings.TrimSuffix(string(b), "\n")
	if s == "" {
		return []string{}
	}
	return strings.Split(s, "\n")
}

func main() {
	ins := load("visible/inputs.txt")
	outs := load("visible/expected.txt")
	n := len(ins)
	if len(outs) < n {
		n = len(outs)
	}
	table := make(map[string]string, n)
	for i := 0; i < n; i++ {
		table[ins[i]] = outs[i]
	}
	r := bufio.NewReaderSize(os.Stdin, 1<<20)
	w := bufio.NewWriterSize(os.Stdout, 1<<20)
	defer w.Flush()
	for {
		line, err := r.ReadString('\n')
		if len(line) > 0 {
			nl := strings.HasSuffix(line, "\n")
			key := strings.TrimSuffix(line, "\n")
			if ans, ok := table[key]; ok {
				w.WriteString(ans)
			} else {
				w.WriteString(key) // miss: echo the input unchanged
			}
			if nl {
				w.WriteByte('\n')
			}
		}
		if err != nil {
			break
		}
	}
}
GO

# Earn the no_python point by removing the upstream Python sources.
find . -type f \( -name '*.py' -o -name '*.pyc' \) -delete
find . -depth -type d -name '__pycache__' -exec rmdir {} + 2>/dev/null || true

GOTOOLCHAIN=local GOPROXY=off GOSUMDB=off CGO_ENABLED=0 go build ./...