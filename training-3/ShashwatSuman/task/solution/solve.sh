#!/bin/bash
# Reference solution (the oracle): install the Go port, then remove the Python.
set -euo pipefail

cd /workspace/repo

cat > go.mod <<'EOF'
module titlecase

go 1.23
EOF

cp /solution/main.go ./main.go

# No .py files may be left anywhere in the repository.
find . -name '*.py' -type f -delete
find . -name '__pycache__' -type d -prune -exec rm -rf {} +
# Remove folders the deletion left empty (e.g. the old titlecase/ package).
find . -mindepth 1 -type d -empty -delete

go build -o /tmp/build-check/ ./...
go build -o /tmp/titlecase .
echo "the lord of the rings" | /tmp/titlecase
