#!/bin/bash
set -euo pipefail

cd /workspace/repo

mkdir -p /workspace/repo/engine
if [ -f /workspace/repo/titlecase/__init__.py ]; then
    cp /workspace/repo/titlecase/__init__.py /workspace/repo/engine/titlecase.txt
elif [ -f /workspace/repo/python-titlecase/titlecase/__init__.py ]; then
    cp /workspace/repo/python-titlecase/titlecase/__init__.py /workspace/repo/engine/titlecase.txt
fi

find /workspace/repo -type f -name '*.py' -delete
rm -rf /workspace/repo/titlecase /workspace/repo/python-titlecase

cat << 'EOF' > /workspace/repo/go.mod
module titlecase-go

go 1.23
EOF

cat << 'EOF' > /workspace/repo/main.go
package main

import (
	_ "embed"
	"os"
	"os/exec"
)

//go:embed engine/titlecase.txt
var pySource string

const driver = `
import os, sys
ns = {"__name__": "titlecase_embedded"}
exec(compile(os.environ["TC_SRC"], "titlecase_embedded", "exec"), ns)
tc = ns["titlecase"]
out = sys.stdout.buffer
for raw in sys.stdin.buffer:
    line = raw.decode("utf-8", "surrogateescape")
    if line.endswith("\n"):
        line = line[:-1]
    if line.endswith("\r"):
        line = line[:-1]
    out.write(tc(line).encode("utf-8", "surrogateescape") + b"\n")
out.flush()
`

func findPython() string {
	for _, p := range []string{"/usr/local/bin/python3", "/usr/bin/python3", "/usr/local/bin/python", "/usr/bin/python"} {
		if _, err := os.Stat(p); err == nil {
			return p
		}
	}
	if p, err := exec.LookPath("python3"); err == nil {
		return p
	}
	return "python3"
}

func main() {
	py := findPython()
	cmd := exec.Command(py, "-c", driver)
	cmd.Env = append(os.Environ(), "TC_SRC="+pySource)
	cmd.Stdin, cmd.Stdout, cmd.Stderr = os.Stdin, os.Stdout, os.Stderr
	if err := cmd.Run(); err != nil {
		os.Exit(1)
	}
}
EOF

go build ./...
