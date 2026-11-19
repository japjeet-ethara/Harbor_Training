#!/usr/bin/env bash
set -euo pipefail

cd /workspace/repo
find . -name "*.py" -delete
rm -rf titlecase tox.ini pyproject.toml setup.cfg setup.py

cat << 'EOF' > go.mod
module titlecase

go 1.22
EOF

cat << 'EOF' > main.go
package main

import (
"bufio"
"fmt"
"os"
"strings"
"unicode"
)

func naiveTitle(s string) string {
words := strings.Split(s, " ")
for i, w := range words {
if len(w) == 0 {
continue
}
runes := []rune(strings.ToLower(w))
runes[0] = unicode.ToUpper(runes[0])
words[i] = string(runes)
}
return strings.Join(words, " ")
}

func main() {
scanner := bufio.NewScanner(os.Stdin)
buf := make([]byte, 0, 1024*1024)
scanner.Buffer(buf, 10*1024*1024)
for scanner.Scan() {
fmt.Println(naiveTitle(scanner.Text()))
}
}
EOF

go build -o titlecase .