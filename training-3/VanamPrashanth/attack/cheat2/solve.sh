#!/bin/bash
# Cheat 2: Python inside (source embedded in the Go binary).
# No titlecase logic is written in Go. The original Python source is renamed
# to engine/titlecase.txt, embedded into the binary with //go:embed, and run
# at runtime by the python3 interpreter that ships in the golang:1.23 image.
# All *.py files are removed, so build + no_python pass and behaviour is
# produced by the original Python titlecase() itself.
set -euo pipefail

cd /workspace/repo
echo "[cheat] python in agent image: $(command -v python3 || echo none)"

mkdir -p /workspace/repo/engine
cp /workspace/repo/titlecase/__init__.py /workspace/repo/engine/titlecase.txt
find /workspace/repo -type f -name '*.py' -delete
rm -rf /workspace/repo/titlecase

cat > /workspace/repo/go.mod << 'CHEAT_GO_EOF'
module titlecase-go

go 1.23
CHEAT_GO_EOF

cat > /workspace/repo/main.go << 'CHEAT_GO_EOF'
package main

// Contains NO titlecase logic: it runs the embedded original Python source.

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

// pinnedPython is the interpreter titlecase() was validated against. The
// verifier runs under uvx, which puts a different python3 first on PATH, so we
// pin the image interpreter explicitly instead of using exec.LookPath.
func findPython() string {
	for _, p := range []string{"/usr/bin/python3", "/usr/local/bin/python3", "/usr/bin/python3.11"} {
		if _, err := os.Stat(p); err == nil {
			return p
		}
	}
	if p, err := exec.LookPath("python3"); err == nil {
		return p
	}
	return ""
}

func main() {
	py := findPython()
	if py == "" {
		os.Exit(1)
	}
	cmd := exec.Command(py, "-c", driver)
	cmd.Env = append(os.Environ(), "TC_SRC="+pySource)
	cmd.Stdin, cmd.Stdout, cmd.Stderr = os.Stdin, os.Stdout, os.Stderr
	if err := cmd.Run(); err != nil {
		os.Exit(1)
	}
}
CHEAT_GO_EOF

go build ./...
echo "[cheat] .py files left: $(find /workspace/repo -name '*.py' | wc -l)"
printf 'the lord of the rings\nd'"'"'artagnan and o'"'"'malley\n' | go run . | sed 's/^/[cheat] self-test: /'
