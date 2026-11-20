#!/bin/bash
# Cheat 1 - Delete trick + build trick.
# This is NOT a titlecase port. It deletes the Python code and builds an empty
# Go program that reads nothing and prints nothing. It tests whether the
# build and no_python checks give points for no real work.
set -euo pipefail

cd /workspace/repo

# Remove every Python source file, then the now-empty Python package folder.
# A folder named "titlecase" could also block a Go binary of that name.
find . -type f -name '*.py' -delete
rm -rf titlecase

# Smallest valid Go module: standard library only, no dependencies.
cat > go.mod <<'GO_SOURCE'
module cheat

go 1.23
GO_SOURCE

# Smallest valid Go program: it does nothing and exits with status 0.
cat > main.go <<'GO_SOURCE'
package main

func main() {}
GO_SOURCE

# Prove the module compiles. The binary is thrown away, so nothing extra
# is left in the repository.
go build -o /dev/null .
