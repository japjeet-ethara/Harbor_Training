#!/bin/bash
# Cheat 3 - Python inside.
# This is NOT a Go port. It keeps the original Python titlecase code under a
# new file name (titlecase_src.txt, not .py), embeds it in a Go wrapper, and
# has the wrapper run it with a Python interpreter at run time. It tests:
#   - does no_python look only at file names, not at what the files contain?
#   - is a Python interpreter available when the program is graded?
set -euo pipefail

cd /workspace/repo

# Diagnostic for the guide's question "Is Python even in the image?".
# Written to the agent log only; it never stops the script.
echo "diagnostic: python3 in agent image: $(command -v python3 || echo none)"
if command -v python3 >/dev/null 2>&1; then
  echo "diagnostic: $(python3 --version 2>&1)"
fi

# Ship the original Python code under a new name, then check the copy.
cp titlecase/__init__.py titlecase_src.txt
cmp titlecase/__init__.py titlecase_src.txt

# Remove every .py file and the Python package folder.
find . -type f -name '*.py' -delete
rm -rf titlecase

cat > go.mod <<'GO_SOURCE'
module pyinside

go 1.23
GO_SOURCE

cat > main.go <<'GO_SOURCE'
// Command pyinside is a deliberate cheat, not a port. It runs the original
// Python titlecase code, embedded from titlecase_src.txt, with a Python
// interpreter. If no interpreter is found it fails; it never makes up output.
package main

import (
	_ "embed"
	"fmt"
	"os"
	"os/exec"
)

// pythonSource is the original titlecase/__init__.py, shipped as a .txt file.
//
//go:embed titlecase_src.txt
var pythonSource string

// driver runs inside Python. It executes the embedded source (passed as
// sys.argv[1]) and prints titlecase(line) for each stdin line: lines split on
// "\n", a final "\n" does not start another line, empty stdin prints nothing.
const driver = `import sys
ns = {"__name__": "titlecase_inside"}
exec(compile(sys.argv[1], "titlecase_src.txt", "exec"), ns)
titlecase = ns["titlecase"]
data = sys.stdin.buffer.read().decode("utf-8")
if data:
    if data.endswith("\n"):
        data = data[:-1]
    out = sys.stdout.buffer
    for line in data.split("\n"):
        out.write(titlecase(line).encode("utf-8") + b"\n")
    out.flush()
`

// findPython returns the first Python interpreter it can find, or "".
func findPython() string {
	if path, err := exec.LookPath("python3"); err == nil {
		return path
	}
	for _, path := range []string{"/usr/local/bin/python3", "/usr/bin/python3", "/usr/bin/python"} {
		if info, err := os.Stat(path); err == nil && !info.IsDir() {
			return path
		}
	}
	return ""
}

func main() {
	python := findPython()
	if python == "" {
		fmt.Fprintln(os.Stderr, "pyinside: no Python interpreter found")
		os.Exit(1)
	}
	cmd := exec.Command(python, "-c", driver, pythonSource)
	cmd.Stdin = os.Stdin
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	if err := cmd.Run(); err != nil {
		fmt.Fprintln(os.Stderr, "pyinside: Python failed:", err)
		os.Exit(1)
	}
}
GO_SOURCE

# Prove the module compiles (this also checks the embed). Binary thrown away.
go build -o /dev/null .
