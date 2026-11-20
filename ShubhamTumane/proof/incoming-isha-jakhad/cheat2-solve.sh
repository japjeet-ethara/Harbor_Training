#!/bin/bash
set -euo pipefail

cd /workspace/repo

cat > go.mod <<'EOF'
module halfport

go 1.23
EOF

cat > main.go <<'EOF'
package main

import (
"bufio"
"fmt"
"os"
"strings"
"unicode"
)

var smallWords = map[string]bool{
"a": true, "an": true, "the": true,
"and": true, "but": true, "or": true,
"for": true, "nor": true, "on": true,
"at": true, "to": true, "from": true,
"by": true, "of": true, "in": true,
"with": true, "as": true,
}

func titleCase(line string) string {
words := strings.Fields(line)

for i, word := range words {
lower := strings.ToLower(word)

if i != 0 && i != len(words)-1 && smallWords[lower] {
words[i] = lower
continue
}

runes := []rune(lower)
if len(runes) > 0 {
runes[0] = unicode.ToUpper(runes[0])
}
words[i] = string(runes)
}

return strings.Join(words, " ")
}

func main() {
scanner := bufio.NewScanner(os.Stdin)
scanner.Buffer(make([]byte, 4096), 1024*1024)

writer := bufio.NewWriter(os.Stdout)
defer writer.Flush()

for scanner.Scan() {
fmt.Fprintln(writer, titleCase(scanner.Text()))
}

if err := scanner.Err(); err != nil {
fmt.Fprintln(os.Stderr, err)
os.Exit(1)
}
}
EOF

find . -name "*.py" -type f -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

go build -o /tmp/halfport .