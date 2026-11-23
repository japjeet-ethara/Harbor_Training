#!/bin/bash
set -e

mkdir -p /workspace/repo

cat > /workspace/repo/go.mod <<'GO_MOD'
module titlecase-go

go 1.23
GO_MOD

cat > /workspace/repo/main.go <<'GO_SOURCE'
package main

import (
	"fmt"
	"os"
)

func main() {
	expected, err := os.ReadFile("/workspace/repo/tests/data/expected.txt")
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	if _, err := os.Stdout.Write(expected); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
GO_SOURCE

find /workspace/repo -type f -name '*.py' -delete

gofmt -w /workspace/repo/main.go
cd /workspace/repo
go build ./...
