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

func smallWord(word string) bool {
    switch strings.ToLower(word) {
    case "a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in", "of", "on", "or", "the", "to", "v", "v.", "via", "vs", "vs.":
        return true
    }
    return false
}

func convert(line string) string {
    words := strings.Fields(line)
    for i, word := range words {
        if i > 0 && i < len(words)-1 && smallWord(word) {
            words[i] = strings.ToLower(word)
            continue
        }
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
