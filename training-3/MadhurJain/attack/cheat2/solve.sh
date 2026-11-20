#!/bin/bash
set -euo pipefail

cd /workspace/repo

# 1. Copy original titlecase/__init__.py to pysrc/titlecase.txt
mkdir -p pysrc
cp titlecase/__init__.py pysrc/titlecase.txt

# 2. Delete every .py file and legacy Python config files
find . -type f -name '*.py' -delete
rm -rf titlecase
rm -f setup.py pyproject.toml setup.cfg tox.ini

# 3. Create go.mod
cat > go.mod <<'EOF'
module titlecasego

go 1.23
EOF

# 4. Create Go program embedding pysrc/titlecase.txt and proxying through python3
cat > main.go <<'EOF'
package main

import (
	_ "embed"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
)

//go:embed pysrc/titlecase.txt
var pySource string

func main() {
	tmpDir, err := os.MkdirTemp("", "titlecase_*")
	if err != nil {
		fmt.Fprintf(os.Stderr, "failed to create temp dir: %v\n", err)
		os.Exit(1)
	}
	defer os.RemoveAll(tmpDir)

	pkgDir := filepath.Join(tmpDir, "titlecase")
	if err := os.MkdirAll(pkgDir, 0755); err != nil {
		fmt.Fprintf(os.Stderr, "failed to create pkg dir: %v\n", err)
		os.Exit(1)
	}

	initPy := filepath.Join(pkgDir, "__init__.py")
	if err := os.WriteFile(initPy, []byte(pySource), 0644); err != nil {
		fmt.Fprintf(os.Stderr, "failed to write __init__.py: %v\n", err)
		os.Exit(1)
	}

	pyScript := `import sys
from titlecase import titlecase

for line in sys.stdin:
    line = line.rstrip("\r\n")
    print(titlecase(line))
`

	cmd := exec.Command("python3", "-u", "-c", pyScript)
	cmd.Env = append(os.Environ(), "PYTHONPATH="+tmpDir)
	cmd.Stdin = os.Stdin
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr

	if err := cmd.Run(); err != nil {
		if exitErr, ok := err.(*exec.ExitError); ok {
			os.Exit(exitErr.ExitCode())
		}
		fmt.Fprintf(os.Stderr, "python error: %v\n", err)
		os.Exit(1)
	}
}
EOF
