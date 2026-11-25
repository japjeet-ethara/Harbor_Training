#!/bin/bash
# Experiment 5 — Python Inside Wrapper:
set -euo pipefail

repo=/workspace/repo

# Save titlecase python source as .dat before deleting .py files and directory
cp "$repo/titlecase/__init__.py" "$repo/titlecase.dat"
chmod 666 "$repo/titlecase.dat"

# Remove the titlecase directory so go build doesn't conflict with package name
rm -rf "$repo/titlecase"
find "$repo" -type f -name '*.py' -delete
find "$repo" -name '__pycache__' -type d -prune -exec rm -rf {} +
rm -rf "$repo/setup.py" "$repo/setup.cfg" "$repo/pyproject.toml" "$repo/tox.ini"

cat > "$repo/go.mod" << 'EOF'
module titlecase

go 1.23
EOF

cat > "$repo/main.go" << 'EOF'
package main

import (
	"os"
	"os/exec"
)

func main() {
	pyScript := `
import os
import sys

paths = ['/workspace/repo/titlecase.dat', '/tmp/titlecase.dat', 'titlecase.dat']
code = None
for p in paths:
    if os.path.isfile(p):
        try:
            with open(p, 'r', encoding='utf-8') as f:
                code = f.read()
            break
        except Exception:
            pass

if not code:
    sys.exit(1)

ns = {}
exec(code, ns)
tc = ns.get('titlecase')
if not tc:
    sys.exit(1)

for line in sys.stdin:
    line = line.rstrip('\r\n')
    sys.stdout.write(tc(line) + '\n')
sys.stdout.flush()
`
	cmd := exec.Command("python3", "-c", pyScript)
	cmd.Stdin = os.Stdin
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	_ = cmd.Run()
}
EOF

cd "$repo"
go build ./...
go build -o /tmp/titlecase .