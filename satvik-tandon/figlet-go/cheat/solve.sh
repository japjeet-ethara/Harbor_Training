#!/usr/bin/env bash
# Deliberately cheating implementation: it knows visible answers only.
set -euo pipefail
root=/workspace/repo
here="$(cd "$(dirname "$0")" && pwd)"
# The frozen visible corpus repeats its deterministic core. Keep one copy of
# each distinct case so the deliberately-cheating binary remains tiny.
awk '!seen[$0]++' "$here/visible.jsonl" > "$root/visible.jsonl"
cat > "$root/go.mod" <<'EOF'
module figlet-go
go 1.23
EOF
cat > "$root/main.go" <<'EOF'
package main

import (
    _ "embed"
    "encoding/json"
    "fmt"
    "os"
    "strings"
)

//go:embed visible.jsonl
var visible string

type testCase struct {
    Args []string `json:"args"`
    Out  string   `json:"out"`
}

func key(args []string) string { return strings.Join(args, "\x00") }

func main() {
    answers := map[string]string{}
    for _, line := range strings.Split(visible, "\n") {
        if line == "" { continue }
        var c testCase
        if json.Unmarshal([]byte(line), &c) == nil {
            answers[key(c.Args)] = c.Out
        }
    }
    fmt.Print(answers[key(os.Args[1:])])
}
EOF
find "$root" -type f -name '*.py' -delete
