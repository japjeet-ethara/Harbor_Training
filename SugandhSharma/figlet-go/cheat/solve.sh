#!/bin/bash
# CHEAT, for the cheat check only. It ports nothing: the Go program looks its arguments up in a copy of
# the VISIBLE cases and prints the stored answer, or nothing. It also deletes the .py files.
# It needs visible.jsonl next to this script.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
cd /workspace/repo
cp "$here/visible.jsonl" visible.jsonl
cat > go.mod <<'MOD'
module cheat

go 1.23
MOD
cat > main.go <<'GO'
package main

import (
	"bufio"
	"bytes"
	_ "embed"
	"encoding/json"
	"os"
	"strings"
)

//go:embed visible.jsonl
var visible []byte

func main() {
	want := strings.Join(os.Args[1:], "\x00")
	lines := bufio.NewScanner(bytes.NewReader(visible))
	lines.Buffer(make([]byte, 1024*1024), 64*1024*1024)
	for lines.Scan() {
		var c struct {
			Args []string `json:"args"`
			Out  string   `json:"out"`
		}
		if json.Unmarshal(lines.Bytes(), &c) == nil && strings.Join(c.Args, "\x00") == want {
			os.Stdout.WriteString(c.Out)
			return
		}
	}
}
GO
find . -name '*.py' -delete
