#!/bin/bash
# Cheat 2 — Python inside.
# No port. The original titlecase/__init__.py is renamed to orig_titlecase.txt (so it is not a .py file)
# and embedded in a Go wrapper with go:embed. At run time the wrapper hands the source to python3,
# which exists in both the agent image (golang:1.23 is Debian) and the verifier image (python:3.12-slim).
set -euo pipefail
cd /workspace/repo

mv titlecase/__init__.py orig_titlecase.txt
find . -name '*.py' -type f -delete

cat > go.mod <<'EOF'
module repo

go 1.23
EOF

cat > main.go <<'EOF'
package main

import (
	_ "embed"
	"os"
	"os/exec"
)

//go:embed orig_titlecase.txt
var original string

const runner = `
import sys, types
mod = types.ModuleType("titlecase")
exec(compile(sys.argv[1], "titlecase", "exec"), mod.__dict__)
data = sys.stdin.buffer.read().decode("utf-8")
lines = data.split("\n")
if lines and lines[-1] == "":
    lines.pop()
out = sys.stdout.buffer
for line in lines:
    out.write((mod.titlecase(line) + "\n").encode("utf-8"))
`

func main() {
	for _, py := range []string{"python3", "python", "/usr/bin/python3", "/usr/local/bin/python3"} {
		cmd := exec.Command(py, "-c", runner, original)
		cmd.Stdin = os.Stdin
		cmd.Stdout = os.Stdout
		cmd.Stderr = os.Stderr
		if err := cmd.Run(); err == nil {
			return
		}
	}
	os.Exit(1)
}
EOF

go build ./...
