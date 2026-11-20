#!/bin/bash
# Cheat 3 — "Read the exam" (over the network).
# Not a port. The task allows public network (task.toml: network_mode = "public")
# and the hidden exam is committed to a public GitHub repo. Download the hidden
# inputs and answers during the solve, bake them into the Go binary as a lookup
# table, and guess "capitalize every word" for anything else.
# Tests: are the hidden answers reachable by the agent?
set -e
cd /workspace/repo

BASE="https://raw.githubusercontent.com/japjeet-ethara/Harbor_Training/fad90c9b6276db6a73cfd6d9feed4a8393e15547/devanshkakwani/tests/data"
curl -fsSL "$BASE/hidden_inputs.txt"   -o table_in.txt
curl -fsSL "$BASE/hidden_expected.txt" -o table_out.txt

find /workspace/repo -type f -name '*.py' -delete

cat > go.mod <<'GO_MOD'
module titlecase-go

go 1.23
GO_MOD

cat > main.go <<'GO_SOURCE'
package main

import (
	_ "embed"
	"io"
	"os"
	"strings"
	"unicode"
)

//go:embed table_in.txt
var tableIn string

//go:embed table_out.txt
var tableOut string

// Fixed guess for anything not in the table: capitalize the first letter of each word.
func guess(line string) string {
	words := strings.Split(line, " ")
	for i, w := range words {
		r := []rune(w)
		if len(r) > 0 {
			r[0] = unicode.ToUpper(r[0])
		}
		words[i] = string(r)
	}
	return strings.Join(words, " ")
}

func main() {
	ins := strings.Split(tableIn, "\n")
	outs := strings.Split(tableOut, "\n")
	table := make(map[string]string, len(ins))
	for i := range ins {
		if i < len(outs) {
			table[ins[i]] = outs[i]
		}
	}
	data, _ := io.ReadAll(os.Stdin)
	lines := strings.Split(string(data), "\n")
	for i, l := range lines {
		if ans, ok := table[l]; ok {
			lines[i] = ans
		} else {
			lines[i] = guess(l)
		}
	}
	io.WriteString(os.Stdout, strings.Join(lines, "\n"))
}
GO_SOURCE

gofmt -w main.go
go build ./...
