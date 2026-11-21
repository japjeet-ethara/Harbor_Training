#!/bin/bash
set -euo pipefail
cd /workspace/repo
find . -type f -name '*.py' -delete
rm -f setup.py pyproject.toml setup.cfg tox.ini
cat > go.mod <<'EOF'
module titlecasego
go 1.23
EOF
cp /solution/main.go /solution/casing.go .
