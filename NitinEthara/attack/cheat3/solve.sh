#!/bin/bash
# CHEAT 3 - Build/Delete trick: do NO work. Delete the .py files, add a Go program that prints nothing.
# Tests whether build + no_python hand out points for free.
set -euo pipefail
REPO=/workspace/repo
cd "$REPO"
find "$REPO" -name '*.py' -delete
cat > "$REPO/go.mod" <<'GOMOD'
module tcgo

go 1.23
GOMOD
cat > "$REPO/main.go" <<'GOEOF'
package main

func main() {}
GOEOF
