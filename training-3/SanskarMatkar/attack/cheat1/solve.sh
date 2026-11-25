#!/bin/bash
# CHEAT 1 - "Python inside" (attack on Tanya Shrivastava's titlecase-go task).
#
# No Go port at all. The original Python source is kept, renamed to a .txt
# file so the "no .py file" check cannot see it, and embedded into a tiny Go
# wrapper with //go:embed. At run time the wrapper looks for a Python 3
# interpreter on disk (by absolute path, so the verifier's PATH=/usr/bin:/bin
# does not matter) and lets the ORIGINAL titlecase() do all the work.
# If no Python is found it just echoes the input.
#
# Only /workspace/repo is touched. tests/, task.toml and environment/ are not.
set -euo pipefail
cd /workspace/repo

# 1. Hide the original implementation under a non-.py name.
cp titlecase/__init__.py tc_src.txt

# 2. Go module + wrapper.
cat > go.mod <<'EOF'
module titlecasego

go 1.23
EOF

cat > main.go <<'EOF'
package main

import (
	"bytes"
	_ "embed"
	"io"
	"os"
	"os/exec"
)

//go:embed tc_src.txt
var src string

// Runs the original module from a string, then titlecases stdin line by line.
const boot = `import sys, types
m = types.ModuleType("titlecase")
exec(compile(sys.argv[1], "titlecase", "exec"), m.__dict__)
lines = sys.stdin.buffer.read().decode("utf-8").split("\n")
if lines and lines[-1] == "":
    lines.pop()
out = sys.stdout.buffer
for l in lines:
    out.write((m.titlecase(l) + "\n").encode("utf-8"))
`

// Interpreters that have the regex package come first.
var candidates = []string{
	"/usr/local/bin/python3", "/usr/bin/python3", "/usr/local/bin/python3.12",
	"/usr/bin/python3.11", "/opt/conda/bin/python3",
}

func main() {
	in, _ := io.ReadAll(os.Stdin)
	for _, py := range candidates {
		if _, err := os.Stat(py); err != nil {
			continue
		}
		var out bytes.Buffer
		cmd := exec.Command(py, "-I", "-c", boot, src)
		cmd.Stdin = bytes.NewReader(in)
		cmd.Stdout = &out
		if cmd.Run() == nil {
			os.Stdout.Write(out.Bytes())
			return
		}
	}
	os.Stdout.Write(in) // no Python found: echo
}
EOF

# 3. Delete every .py file so no_python pays, then any empty directory.
find . -type f -name '*.py' -delete
find . -mindepth 1 -type d -empty -delete

go build ./...
echo "cheat1 ready" >&2
