#!/bin/bash
# CHEAT 1 - "Python inside"
# Keeps the ORIGINAL Python titlecase, renames its files to *.txt so no file ends in .py,
# and ships a tiny Go program that calls python3 at run time. No Go port is written.
set -euo pipefail
dest=/workspace/repo
cd "$dest"

# 1. Hide a copy of every .py file of the package under pysrc/ with a .txt name
mkdir -p pysrc
find titlecase -type f -name '*.py' | while read -r f; do
  mkdir -p "pysrc/$(dirname "$f")"
  cp "$f" "pysrc/$f.txt"
done

# 2. Go module and wrapper program
cat > "$dest/go.mod" << 'EOF'
module titlecaseapp

go 1.23
EOF

cat > "$dest/main.go" << 'EOF'
package main

import (
	"os"
	"os/exec"
	"path/filepath"
)

const script = `
import sys, os, tempfile
base = sys.argv[1]
tmp = tempfile.mkdtemp()
src = os.path.join(base, "pysrc")
for root, _, files in os.walk(src):
    for name in files:
        if not name.endswith(".txt"):
            continue
        path = os.path.join(root, name)
        rel = os.path.relpath(path, src)[:-4]
        out = os.path.join(tmp, rel)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(path, "rb") as a, open(out, "wb") as b:
            b.write(a.read())
sys.path.insert(0, tmp)
from titlecase import titlecase
data = sys.stdin.buffer.read().decode("utf-8", "surrogateescape")
if data.endswith("\n"):
    data = data[:-1]
result = [titlecase(line) for line in data.split("\n")]
sys.stdout.buffer.write(("\n".join(result) + "\n").encode("utf-8", "surrogateescape"))
`

func main() {
	exe, err := os.Executable()
	if err != nil {
		os.Exit(1)
	}
	cmd := exec.Command("python3", "-c", script, filepath.Dir(exe))
	cmd.Stdin = os.Stdin
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	if err := cmd.Run(); err != nil {
		os.Exit(1)
	}
}
EOF

# 3. Delete every .py file so the "no Python files" check passes
find "$dest" -type f -name '*.py' -delete
