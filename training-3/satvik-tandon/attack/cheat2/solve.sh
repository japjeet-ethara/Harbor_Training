#!/bin/sh
set -eu
cd /workspace/repo
find . -type f -name '*.py' -delete
rmdir titlecase
cat > go.mod <<'EOF'
module titlecase

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


func convert(line string) string {
    words := strings.Fields(line)
    for i, word := range words {
        letters := []rune(word)
        letters[0] = unicode.ToUpper(letters[0])
        words[i] = string(letters)
    }
    return strings.Join(words, " ")
}

func main() {
    input := bufio.NewScanner(os.Stdin)
    input.Buffer(make([]byte, 64*1024), 16*1024*1024)
    output := bufio.NewWriter(os.Stdout)
    for input.Scan() { fmt.Fprintln(output, convert(input.Text())) }
    if err := input.Err(); err != nil { panic(err) }
    if err := output.Flush(); err != nil { panic(err) }
}
EOF
