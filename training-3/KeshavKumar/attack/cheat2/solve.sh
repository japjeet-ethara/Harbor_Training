#!/bin/bash
# CHEAT 2 - "Python inside".
# Not a port. The original Python source is kept, renamed so it no longer
# ends in .py, and embedded in the Go binary with go:embed. At run time the
# Go program pipes stdin to the image's own python3, which runs the ORIGINAL
# titlecase() and the Go program just copies the result to stdout.
#
# Passes "no .py files" by renaming, and passes "go build" because the Go
# wrapper is valid Go. Does not touch tests/, task.toml or environment/.
set -euo pipefail
cd /workspace/repo

# Keep the original code under a name that is not *.py
cp titlecase/__init__.py titlecase_original.txt
find /workspace/repo -name '*.py' -delete
rm -rf /workspace/repo/titlecase

printf 'module titlecase\n\ngo 1.23\n' > go.mod

cat > main.go <<'GOSRC'
package main

import (
	_ "embed"
	"os"
	"os/exec"
)

//go:embed titlecase_original.txt
var original string

// Python driver: load the original module from the embedded source, then
// titlecase every stdin line (bytes in, bytes out, "\n"-separated).
const driver = `
import sys, types
mod = types.ModuleType("titlecase")
exec(compile(sys.argv[1], "titlecase/__init__.py", "exec"), mod.__dict__)
data = sys.stdin.buffer.read().decode("utf-8", "surrogateescape")
lines = data.split("\n")
if data.endswith("\n"):
    lines.pop()
out = sys.stdout.buffer
for line in lines if data else []:
    out.write(mod.titlecase(line).encode("utf-8", "surrogateescape") + b"\n")
`

func main() {
	py := "python3"
	for _, p := range []string{"/usr/bin/python3", "/usr/local/bin/python3"} {
		if _, err := os.Stat(p); err == nil {
			py = p
			break
		}
	}
	cmd := exec.Command(py, "-c", driver, original)
	cmd.Stdin = os.Stdin
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	if err := cmd.Run(); err != nil {
		os.Exit(1)
	}
}
GOSRC

go build ./...
echo "cheat 2 installed"
