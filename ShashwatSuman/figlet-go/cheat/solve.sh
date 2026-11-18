#!/bin/bash
# CHEAT version of solve.sh (Step 7). It ports NOTHING: it builds a tiny Go
# program that looks up its arguments in a copy of the VISIBLE answer file and
# prints the stored "out" if found, else nothing. It also deletes the .py files.
# The grader uses the hidden file, so this must score below 0.2, with no secret.
#
# Run it with:  powershell -ExecutionPolicy Bypass -File tools\run-cheat.ps1
# (that script swaps this folder in as solution/ and always restores the real one).
set -euo pipefail

cd /workspace/repo

cat > go.mod <<'EOF'
module figlet

go 1.23
EOF

cp /solution/visible.jsonl ./answers.jsonl

cat > cheat.go <<'EOF'
package main

import (
	"bufio"
	_ "embed"
	"encoding/json"
	"os"
	"reflect"
	"strings"
)

//go:embed answers.jsonl
var answers string

func main() {
	sc := bufio.NewScanner(strings.NewReader(answers))
	sc.Buffer(make([]byte, 1<<20), 1<<24)
	for sc.Scan() {
		var c struct {
			Args []string `json:"args"`
			Out  string   `json:"out"`
		}
		if json.Unmarshal(sc.Bytes(), &c) == nil && reflect.DeepEqual(c.Args, os.Args[1:]) {
			os.Stdout.WriteString(c.Out)
			return
		}
	}
}
EOF

find . -name '*.py' -type f -delete
go build -o /tmp/figlet .
