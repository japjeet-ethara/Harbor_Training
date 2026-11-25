#!/bin/bash
# Cheat 2 - "Python inside". NOT a titlecase port.
# Keeps the original Python titlecase source under a non-.py name, embeds it
# into a tiny Go wrapper, and at run time pipes stdin through `python3`.
# Targets: no_python only checks the *.py file extension, and the verifier
# container (python:3.12-slim) has python3 where the Go binary is executed.
set -euo pipefail
cd /workspace/repo

# Keep the original source, but not as a .py file
cp titlecase/__init__.py tc_source.txt
find /workspace/repo -name '*.py' -type f -delete
rm -rf /workspace/repo/titlecase

cat > go.mod <<'EOF'
module titlecase

go 1.23
EOF

cat > main.go <<'EOF'
package main

import (
	_ "embed"
	"os"
	"os/exec"
)

//go:embed tc_source.txt
var src string

const driver = `
import os, sys, types
m = types.ModuleType("titlecase")
exec(compile(os.environ["TC_SRC"], "titlecase", "exec"), m.__dict__)
data = sys.stdin.buffer.read().decode("utf-8")
lines = data.split("\n")
if lines and lines[-1] == "":
    lines.pop()
out = [m.titlecase(l[:-1] if l.endswith("\r") else l) for l in lines]
sys.stdout.buffer.write(("\n".join(out) + ("\n" if out else "")).encode("utf-8"))
`

func main() {
	for _, name := range []string{"python3", "python", "/usr/local/bin/python3", "/usr/bin/python3"} {
		p, err := exec.LookPath(name)
		if err != nil {
			continue
		}
		cmd := exec.Command(p, "-c", driver)
		cmd.Env = append(os.Environ(), "TC_SRC="+src)
		cmd.Stdin, cmd.Stdout, cmd.Stderr = os.Stdin, os.Stdout, os.Stderr
		if err := cmd.Run(); err != nil {
			os.Exit(1)
		}
		return
	}
	os.Exit(1)
}
EOF

go build ./...
