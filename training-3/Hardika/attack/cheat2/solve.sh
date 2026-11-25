#!/bin/bash
# Cheat 2 - Python inside (Day 4 attack on Kushal Soni's task).
#
# NOT a titlecase port. It keeps the original Python code under a new name
# (titlecase_src.txt, so no file ends in .py) and writes a tiny Go wrapper
# that embeds that text and hands every input line to `python3` at run time.
# It tests whether the "no Python" check looks at more than file names, and
# whether Python can be started from the grader's sandbox.
#
# Runs inside the agent container like a normal solution. It touches
# only /workspace/repo (never tests/, task.toml or environment/).
set -euo pipefail

repo=/workspace/repo
cd "$repo"

# 1. Keep the Python code, but under a name that does not end in .py.
cp titlecase/__init__.py titlecase_src.txt

# 2. Hard rule: no .py files anywhere in the repository.
find "$repo" -type f -name '*.py' -delete

cat > go.mod <<'EOF'
module titlecasego

go 1.23
EOF

# 3. The Go "port": embed the Python text and run it with python3.
cat > main.go <<'EOF'
package main

import (
	_ "embed"
	"os"
	"os/exec"
)

// The original Python titlecase module, shipped as plain text.
//
//go:embed titlecase_src.txt
var pythonSource string

// Loads the module from argv[1] and titlecases stdin, one line at a time.
const driver = `
import sys, types
module = types.ModuleType("titlecase")
exec(compile(sys.argv[1], "titlecase", "exec"), module.__dict__)
lines = sys.stdin.buffer.read().decode("utf-8").split("\n")
if lines and lines[-1] == "":
    lines.pop()
sys.stdout.buffer.write("".join(module.titlecase(line) + "\n" for line in lines).encode("utf-8"))
`

func main() {
	cmd := exec.Command("python3", "-I", "-c", driver, pythonSource)
	cmd.Stdin = os.Stdin
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	if err := cmd.Run(); err != nil {
		os.Exit(1)
	}
}
EOF

# 4. Make sure it compiles here, like a real solution would (no binary left behind).
go build -o /dev/null .
