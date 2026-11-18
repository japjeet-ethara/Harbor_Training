#!/bin/bash
# Reference solution (the "oracle"): a standard-library-only Go port of
# python-titlecase, written to /workspace/repo, after which every Python file
# is removed.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
cd /workspace/repo

cp "$HERE/main.go" ./main.go

cat > go.mod <<'EOF'
module titlecasego

go 1.23
EOF

# The port is done: delete every Python file, then any directory left empty.
find . -type f -name '*.py' -delete
find . -mindepth 1 -type d -empty -not -path './.git/*' -delete

gofmt -l . | (! grep .) || { echo "gofmt: unformatted files" >&2; exit 1; }
go build ./...
