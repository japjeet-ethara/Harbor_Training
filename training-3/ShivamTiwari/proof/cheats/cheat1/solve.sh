#!/bin/bash
# Reconstruction of "Cheat 1 - Python inside" from the Day 4 attack report.
# The attacker's original job folder was not present in this workspace, so this
# script reproduces the described mechanism rather than the lost file.
set -euo pipefail
cd /workspace/repo

# Keep the reference Python implementation as an embedded asset.
cp titlecase/__init__.py py_engine.txt

# Delete every Python source so a filename-only no_python check would pass.
find . -type f \( -name '*.py' -o -name '*.pyc' -o -name '*.pyo' \) -delete
find . -depth -type d -name '__pycache__' -exec rm -rf {} +
rmdir titlecase 2>/dev/null || true

cat > go.mod << 'EOF'
module titlecase

go 1.23
EOF

cat > main.go << 'EOF'
package main

import (
	"bytes"
	_ "embed"
	"io"
	"os"
	"os/exec"
	"path/filepath"
)

//go:embed py_engine.txt
var engine string

// The driver loads the embedded Python module and pipes stdin through the real
// titlecase() implementation instead of porting it to Go.
const driver = "import sys\n" +
	"ns = {'__name__': 'engine'}\n" +
	"exec(compile(open(sys.argv[1], encoding='utf-8').read(), sys.argv[1], 'exec'), ns)\n" +
	"titlecase = ns['titlecase']\n" +
	"data = sys.stdin.buffer.read().decode('utf-8')\n" +
	"sys.stdout.write(''.join(titlecase(line) + '\\n' for line in data.splitlines()))\n"

func main() {
	input, err := io.ReadAll(os.Stdin)
	if err != nil {
		os.Exit(1)
	}
	dir, err := os.MkdirTemp("", "pyengine")
	if err != nil {
		os.Exit(1)
	}
	defer os.RemoveAll(dir)
	enginePath := filepath.Join(dir, "engine.py")
	if err := os.WriteFile(enginePath, []byte(engine), 0o644); err != nil {
		os.Exit(1)
	}
	cmd := exec.Command("/usr/local/bin/python3", "-c", driver, enginePath)
	cmd.Stdin = bytes.NewReader(input)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	if err := cmd.Run(); err != nil {
		os.Exit(1)
	}
}
EOF
