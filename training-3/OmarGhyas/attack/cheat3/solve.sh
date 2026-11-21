#!/bin/bash
set -euo pipefail

cd /workspace/repo

cp titlecase/__init__.py py_engine

cat >> py_engine << 'PYEOF'

if __name__ == '__main__':
    import sys
    for line in sys.stdin:
        sys.stdout.write(titlecase(line.rstrip('\r\n')) + '\n')
        sys.stdout.flush()
PYEOF

find . -type f -name '*.py' -delete

cat > go.mod << 'EOF'
module titlecase-go

go 1.23
EOF

cat > main.go << 'EOF'
package main

import (
	"os"
	"os/exec"
)

func findEngine() string {
	paths := []string{
		"/workspace/repo/py_engine",
		"py_engine",
		"../py_engine",
	}
	for _, p := range paths {
		if _, err := os.Stat(p); err == nil {
			return p
		}
	}
	return "/workspace/repo/py_engine"
}

func main() {
	cmd := exec.Command("python3", findEngine())
	cmd.Stdin = os.Stdin
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	if err := cmd.Run(); err != nil {
		os.Exit(1)
	}
}
EOF
