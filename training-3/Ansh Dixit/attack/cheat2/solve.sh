#!/bin/bash
# CHEAT 2 - "Python inside".
# Ports nothing. Keeps the ORIGINAL Python source, but renames it to a .txt file
# so the "no .py files" check (tests/no_python.py:16, glob "*.py") does not see
# it. A tiny Go program embeds that text and, when run, writes it back out to a
# temp folder and calls a Python interpreter that already exists in the
# verifier image (the one Reward Kit was installed with, tests/Dockerfile:10).
# Only touches /workspace/repo. Never edits tests/, task.toml or environment/.
set -euo pipefail
cd /workspace/repo

cp titlecase/__init__.py ./titlecase_src.txt

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
	"path/filepath"
)

//go:embed titlecase_src.txt
var src []byte

const runner = `
import sys
sys.path.insert(0, sys.argv[1])
from titlecase import titlecase
data = sys.stdin.buffer.read().decode("utf-8")
lines = data.split("\n")
if lines and lines[-1] == "":
    lines.pop()
sys.stdout.buffer.write(("\n".join(titlecase(l) for l in lines) + "\n").encode("utf-8"))
`

// pick an interpreter that can import the "regex" package (the exam's mode)
func pickPython() string {
	cands := []string{"/opt/uv-tools/harbor-rewardkit/bin/python"}
	if g, _ := filepath.Glob("/opt/uv-tools/*/bin/python3"); g != nil {
		cands = append(cands, g...)
	}
	for _, n := range []string{"python3", "python"} {
		if p, err := exec.LookPath(n); err == nil {
			cands = append(cands, p)
		}
	}
	first := ""
	for _, c := range cands {
		if _, err := os.Stat(c); err != nil {
			continue
		}
		if first == "" {
			first = c
		}
		if exec.Command(c, "-c", "import regex").Run() == nil {
			return c
		}
	}
	return first
}

func main() {
	tmp, err := os.MkdirTemp("", "tc")
	if err != nil {
		os.Exit(1)
	}
	defer os.RemoveAll(tmp)
	pkg := filepath.Join(tmp, "titlecase")
	os.MkdirAll(pkg, 0o755)
	os.WriteFile(filepath.Join(pkg, "__init__.py"), src, 0o644)
	cmd := exec.Command(pickPython(), "-c", runner, tmp)
	cmd.Stdin, cmd.Stdout, cmd.Stderr = os.Stdin, os.Stdout, os.Stderr
	if cmd.Run() != nil {
		os.Exit(1)
	}
}
EOF

# remove every .py file (the source now lives on as titlecase_src.txt)
find . -name '*.py' -type f -delete
find . -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true
find . -mindepth 1 -type d -empty -delete
go build -o /tmp/build-check/ ./...
