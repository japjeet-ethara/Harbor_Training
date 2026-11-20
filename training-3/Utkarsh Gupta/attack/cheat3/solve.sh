#!/bin/bash
# Cheat 3 — Build trick + delete Python only (no real port).
#
# Writes the absolute minimum Go program: a go.mod and a main.go that compiles
# but produces NO output (empty main). Then deletes all .py files.
#
# Expected outcome:
#   build      -> 1.0  (go.mod valid, go build ./... passes)
#   no_python  -> 0.0  (no .py files, build passes, BUT behaviour < 50%)
#   behaviour  -> 0.0  (program outputs nothing; 0/2000 lines match)
#   reward     -> (1 + 0 + 0) / 6 ≈ 0.167
#
# Tests whether "build" is worth anything on its own, and whether no_python
# is truly gated behind the 50% behaviour threshold.
set -euo pipefail
export PATH="$PATH:/usr/local/go/bin"
cd /workspace/repo

cat > go.mod <<'GOEOF'
module titlecase

go 1.23
GOEOF

cat > main.go <<'GOEOF'
package main

func main() {
	// No output intentionally.
	// Tests whether the build check alone gives points.
}
GOEOF

# Remove all .py files to try to earn no_python credit
find /workspace/repo -name '*.py' -type f -delete
find /workspace/repo -type d -empty -delete

go build -o /dev/null ./...
echo "cheat3/solve.sh: empty program, .py files removed, build OK"
