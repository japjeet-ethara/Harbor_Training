#!/usr/bin/env bash
set -euo pipefail

cd /workspace/repo
rm -rf titlecase
find /workspace/repo -name "*.py" -delete

cat << 'EOF' > go.mod
module port

go 1.23
EOF

cat << 'EOF' > main.go
package main

import (
"io"
"os"
"strings"
"unicode"
)

var small = map[string]bool{
"a": true, "an": true, "and": true, "as": true, "at": true,
"but": true, "by": true, "en": true, "for": true, "if": true,
"in": true, "of": true, "on": true, "or": true, "the": true,
"to": true, "v": true, "v.": true, "via": true, "vs": true, "vs.": true,
}

func splitLines(s string) []string {
if s == "" {
return nil
}
var lines []string
start := 0
for i := 0; i < len(s); i++ {
if s[i] == '\r' {
lines = append(lines, s[start:i])
if i+1 < len(s) && s[i+1] == '\n' {
i++
}
start = i + 1
} else if s[i] == '\n' {
lines = append(lines, s[start:i])
start = i + 1
}
}
if start < len(s) {
lines = append(lines, s[start:])
}
return lines
}

func capWord(w string) string {
r := []rune(strings.ToLower(w))
for i, ch := range r {
if unicode.IsLetter(ch) {
r[i] = unicode.ToUpper(ch)
break
}
}
return string(r)
}

func titleLine(line string) string {
var out strings.Builder
i := 0
wordIdx := 0
for i < len(line) {
if line[i] == ' ' || line[i] == '\t' {
out.WriteByte(line[i])
i++
continue
}
j := i
for j < len(line) && line[j] != ' ' && line[j] != '\t' {
j++
}
tok := line[i:j]
low := strings.ToLower(tok)
if wordIdx > 0 && j < len(line) && small[low] {
out.WriteString(low)
} else {
out.WriteString(capWord(tok))
}
wordIdx++
i = j
}
return out.String()
}

func main() {
in, err := io.ReadAll(os.Stdin)
if err != nil {
os.Exit(1)
}
var out strings.Builder
for _, line := range splitLines(string(in)) {
out.WriteString(titleLine(line))
out.WriteByte('\n')
}
os.Stdout.WriteString(out.String())
}
EOF