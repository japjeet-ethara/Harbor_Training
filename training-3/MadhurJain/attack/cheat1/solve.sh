#!/bin/bash
set -euo pipefail

cd /workspace/repo

find . -type f -name '*.py' -delete
rm -f setup.py pyproject.toml setup.cfg tox.ini

cat > go.mod <<'EOF'
module titlecasego
go 1.23
EOF

cat > main.go <<'EOF'
package main

import (
	"bufio"
	"fmt"
	"os"
)

func main() {
	s := bufio.NewScanner(os.Stdin)
	for s.Scan() {
		fmt.Println(s.Text())
	}
}
EOF
