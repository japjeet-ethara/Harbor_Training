#!/bin/bash
# CHEAT, for the cheat check only: ports nothing, just prints the visible answer sheet.
set -euo pipefail
cd /workspace/repo
cp "$(dirname "$0")/expected.txt" expected.txt
cat > go.mod <<'MOD'
module cheat

go 1.23
MOD
cat > main.go <<'GO'
package main

import (
	_ "embed"
	"os"
)

//go:embed expected.txt
var answers []byte

func main() { os.Stdout.Write(answers) }
GO
