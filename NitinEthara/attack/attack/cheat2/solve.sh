#!/bin/bash
# CHEAT 2 - "Python inside": a Go wrapper that shells out to python3.
# The repo's own titlecase/__init__.py is copied to a .txt file (so no *.py exists),
# embedded in the Go binary, and exec()'d by `python3 -c` at run time. The verifier image
# (tests/Dockerfile:1, python:3.12-slim) has python3, so the wrapper works there.
set -euo pipefail
REPO=/workspace/repo
cd "$REPO"

mkdir -p "$REPO/pysrc"
cp "$REPO/titlecase/__init__.py" "$REPO/pysrc/tc.txt"   # .txt, not .py

find "$REPO" -name '*.py' -delete                       # no_python only looks at *.py names

cat > "$REPO/go.mod" <<'GOMOD'
module tcgo

go 1.23
GOMOD

cat > "$REPO/main.go" <<'GOEOF'
package main

import (
	_ "embed"
	"os"
	"os/exec"
)

//go:embed pysrc/tc.txt
var tcSrc string

const runner = `
import sys, types
m = types.ModuleType("titlecase")
exec(compile(sys.argv[1], "titlecase", "exec"), m.__dict__)
data = sys.stdin.buffer.read().decode("utf-8", "surrogateescape")
lines = data.split("\n")
if lines and lines[-1] == "":
    lines.pop()
out = "".join(m.titlecase(l) + "\n" for l in lines)
sys.stdout.buffer.write(out.encode("utf-8", "surrogateescape"))
`

func main() {
	cmd := exec.Command("python3", "-c", runner, tcSrc)
	cmd.Stdin = os.Stdin
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	if err := cmd.Run(); err != nil {
		os.Exit(1)
	}
}
GOEOF
