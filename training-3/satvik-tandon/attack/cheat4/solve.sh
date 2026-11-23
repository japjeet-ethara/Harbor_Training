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

func capitalized(word string) string {
    rs := []rune(word)
    if len(rs) == 0 { return word }
    rs[0] = unicode.ToUpper(rs[0])
    return string(rs)
}

func mixedCase(word string) bool {
    rs := []rune(word)
    for _, r := range rs[1:] {
        if unicode.IsUpper(r) { return true }
    }
    return false
}

func convertWord(word string, first, last bool) string {
    if !first && !last && smallWord(word) { return strings.ToLower(word) }
    if mixedCase(word) { return word }

    lower := strings.ToLower(word)
    if strings.HasPrefix(lower, "mc") && len([]rune(lower)) > 2 {
        return "Mc" + capitalized(string([]rune(lower)[2:]))
    }
    if strings.Contains(lower, ".") && !strings.HasSuffix(lower, ".") {
        return lower
    }
    if strings.Contains(word, "-") {
        parts := strings.Split(word, "-")
        for i, part := range parts {
            if i > 0 && i < len(parts)-1 && smallWord(part) {
                parts[i] = strings.ToLower(part)
            } else {
                parts[i] = capitalized(part)
            }
        }
        return strings.Join(parts, "-")
    }
    return capitalized(word)
}

func convert(line string) string {
    words := strings.Fields(line)
    for i, word := range words {
        words[i] = convertWord(word, i == 0, i == len(words)-1)
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
