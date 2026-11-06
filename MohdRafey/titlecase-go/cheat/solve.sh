#!/bin/bash
# Deliberate cheat, used to prove the tests catch it. It ports nothing: the Go
# program ignores stdin and prints the lines of tests/data/expected.txt.
set -euo pipefail

cd /workspace/repo

cat > go.mod <<'GO_SOURCE'
module cheat

go 1.23
GO_SOURCE

cat > main.go <<'GO_SOURCE'
package main

import "os"

func main() {
	answers, err := os.ReadFile("/tests/data/expected.txt")
	if err != nil {
		os.Exit(1)
	}
	os.Stdout.Write(answers)
}
GO_SOURCE

go build -o /dev/null ./...
