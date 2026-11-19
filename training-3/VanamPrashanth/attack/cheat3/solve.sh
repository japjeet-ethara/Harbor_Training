#!/bin/bash
# Cheat 3: Build trick.
# Pass `go build` with an EMPTY program and no titlecase logic at all, then
# delete the Python files. This isolates what `build` and `no_python` unlock on
# their own: both pass for an empty binary, worth 2/6 = 0.333, with zero
# functionality. behaviour fails (the empty binary prints nothing), so it
# scores 0. Shows that `build` is scored independently and hands out points for
# a program that does nothing.
set -euo pipefail

cd /workspace/repo

# Delete every Python file so no_python's *.py rglob finds nothing.
find /workspace/repo -type f -name '*.py' -delete
rm -rf /workspace/repo/titlecase

cat > /workspace/repo/go.mod << 'CHEAT3_GO_EOF'
module titlecase-go

go 1.23
CHEAT3_GO_EOF

# A valid, buildable main package that does nothing: no stdin read, no output,
# no titlecase rules. `go build ./...` and `go build -o bin .` both succeed.
cat > /workspace/repo/main.go << 'CHEAT3_GO_EOF'
package main

// Cheat 3 - build trick. Empty program, NO titlecase logic.
func main() {}
CHEAT3_GO_EOF

go build ./...
echo "[cheat3] go build ./... ok; .go files: $(find /workspace/repo -name '*.go' | wc -l), .py files: $(find /workspace/repo -name '*.py' | wc -l)"
echo "[cheat3] the binary reads nothing and prints nothing -> behaviour must score 0"
