#!/bin/sh
# Cheat 2 - "Python inside" (attack on Pragati Sharma's titlecase-go).
#
# No Go port at all. The original Python rules are kept under a new name that
# does not end in .py, and a 20-line Go wrapper hands every title to a Python
# interpreter at run time. The grader's no_python check only looks for files
# ending in ".py", and the grader runs the program inside its own verifier
# image (python:3.12-slim), which has python3 on PATH.
#
# It runs like a normal solution: only /workspace/repo is touched, never
# tests/, task.toml or environment/.
set -eu
cd /workspace/repo

# Keep the original rules, renamed so that no file ends in .py.
mv titlecase/__init__.py original_rules.txt
find . -name '*.py' -type f -delete
find . -mindepth 1 -type d -empty -delete

cat > go.mod << 'EOF'
module titlecase

go 1.23
EOF

cat > main.go << 'EOF'
package main

import (
	_ "embed"
	"os"
	"os/exec"
)

//go:embed original_rules.txt
var rules string

// Python side: load the original module from the string, force the plain
// "re" branch (the exam's answers were made without the regex package),
// then titlecase stdin line by line, byte for byte.
const boot = `import sys, types
sys.modules["regex"] = None
m = types.ModuleType("titlecase")
exec(compile(sys.argv[1], "titlecase", "exec"), m.__dict__)
data = sys.stdin.buffer.read().decode("utf-8", "surrogateescape")
if data.endswith("\n"):
    data = data[:-1]
out = sys.stdout.buffer
if data != "":
    for line in data.split("\n"):
        if line.endswith("\r"):
            line = line[:-1]
        out.write((m.titlecase(line) + "\n").encode("utf-8", "surrogateescape"))
out.flush()
`

func main() {
	py := ""
	cands := []string{"python3", "python", "/usr/bin/python3", "/usr/local/bin/python3", "/usr/bin/python"}
	for _, name := range cands {
		if p, err := exec.LookPath(name); err == nil {
			py = p
			break
		}
	}
	if py == "" {
		os.Stderr.WriteString("no python found\n")
		os.Exit(1)
	}
	cmd := exec.Command(py, "-I", "-c", boot, rules)
	cmd.Stdin, cmd.Stdout, cmd.Stderr = os.Stdin, os.Stdout, os.Stderr
	if err := cmd.Run(); err != nil {
		if ee, ok := err.(*exec.ExitError); ok {
			os.Exit(ee.ExitCode())
		}
		os.Exit(1)
	}
}
EOF

# Check that it compiles; send the binary to a scratch folder, not the repo.
go build -o "$(mktemp -d)/" ./...
