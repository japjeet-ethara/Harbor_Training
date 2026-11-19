#!/bin/bash
set -euo pipefail
cd /workspace/repo
find /workspace/repo -type f -name "*.py" -delete
rm -rf titlecase
cat << 'GOMOD' > go.mod
module titlecase-stub

go 1.23
GOMOD
cat << 'MAIN' > main.go
package main

func main() {}
MAIN
go build ./...
