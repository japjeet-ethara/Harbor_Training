#!/bin/sh
set -eu
cd /workspace/repo
# Deliberately retain the original .py files: this negative control must receive
# no no_python point. A building Python-free cheat has a mathematical 1/3 floor.
cat > go.mod <<'MOD'
module titlecase-replay

go 1.23.0
MOD
cp visible/expected.txt replay.txt
cat > main.go <<'GO'
package main

import (
    _ "embed"
    "os"
)

//go:embed replay.txt
var visibleAnswers string

func main() {
    if _, err := os.Stdout.WriteString(visibleAnswers); err != nil {
        os.Exit(1)
    }
}
GO
GOTOOLCHAIN=local GOPROXY=off GOSUMDB=off CGO_ENABLED=0 go build ./...
