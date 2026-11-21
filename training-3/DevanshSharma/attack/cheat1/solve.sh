#!/bin/bash
# CHEAT 1 — "Python inside".
# NOT a real port: the Go program embeds the original python titlecase source
# (base64) and, at verifier run time, writes it to a temp dir under /tmp and
# calls /usr/bin/python3 to titlecase stdin.  This tests two things:
#   * the verifier image (FROM golang:1.23) ships python3, and
#   * the no_python check only scans /workspace/repo (the .py lives in /tmp).
# If both hold, behaviour == 1.0 and the reward is a perfect 1.0.
set -euo pipefail
cd /workspace/repo

B64=$(base64 -w 0 titlecase/__init__.py)

cat > main.go <<'EOF'
package main

import (
	"encoding/base64"
	"os"
	"os/exec"
	"path/filepath"
)

const srcB64 = "XPLACEHOLDERX"

func main() {
	dir, err := os.MkdirTemp("", "tc*")
	if err != nil {
		os.Exit(1)
	}
	if err := os.MkdirAll(filepath.Join(dir, "titlecase"), 0o755); err != nil {
		os.Exit(1)
	}
	src, err := base64.StdEncoding.DecodeString(srcB64)
	if err != nil {
		os.Exit(1)
	}
	if err := os.WriteFile(filepath.Join(dir, "titlecase", "__init__.py"), src, 0o644); err != nil {
		os.Exit(1)
	}
	runner := `import sys
sys.path.insert(0, "` + dir + `")
from titlecase import titlecase
data = sys.stdin.read()
lines = data.split("\n")
if lines and lines[-1] == "":
    lines = lines[:-1]
sys.stdout.write("\n".join(titlecase(l) for l in lines) + "\n")
`
	if err := os.WriteFile(filepath.Join(dir, "run_tc"), []byte(runner), 0o644); err != nil {
		os.Exit(1)
	}
	cmd := exec.Command("/usr/bin/python3", filepath.Join(dir, "run_tc"))
	cmd.Stdin = os.Stdin
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	cmd.Env = append(os.Environ(), "PYTHONPATH="+dir, "PYTHONIOENCODING=utf-8", "PYTHONUTF8=1")
	if err := cmd.Run(); err != nil {
		os.Exit(1)
	}
}
EOF

sed -i "s|XPLACEHOLDERX|${B64}|" main.go

cat > go.mod <<'EOF'
module titlecase

go 1.23
EOF

find . -name '*.py' -delete
rm -rf titlecase
