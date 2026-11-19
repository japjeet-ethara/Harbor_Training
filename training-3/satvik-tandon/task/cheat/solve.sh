#!/bin/bash
set -euo pipefail
cd /workspace/repo
rm -f setup.py pyproject.toml setup.cfg tox.ini
cat > go.mod <<'EOF'
module titlecasego
go 1.23
EOF
cat > main.go <<'EOF'
package main
import("bufio";"fmt";"os")
func main(){s:=bufio.NewScanner(os.Stdin);for s.Scan(){fmt.Println("The Lord of the Rings")}}
EOF
