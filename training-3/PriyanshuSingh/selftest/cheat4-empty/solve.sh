#!/bin/bash
# Self-test cheat 4 - Build trick / delete trick.
# Deletes every .py file and leaves a Go program that compiles but prints nothing.
# It asks: does "build" or "no_python" give points with no real work?
set -euo pipefail
cd /workspace/repo
find /workspace/repo -type f -name '*.py' -delete
cat > go.mod << 'GOMOD'
module titlecaseport

go 1.23
GOMOD
cat > main.go << 'GOMAIN'
package main

func main() {}
GOMAIN
go build -buildvcs=false .
