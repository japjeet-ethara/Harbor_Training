#!/bin/sh
set -eu
cd /workspace/repo

if [ ! -f go.mod ]; then
    go mod init titlecase
fi

cat > main.go <<'GO'
package main

func main() {}
GO

go build ./...
