#!/bin/bash
set -euo pipefail

cd /workspace/repo

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

var smallWords = map[string]bool{
    "a": true, "an": true, "the": true,
    "and": true, "but": true, "or": true,
    "for": true, "nor": true, "on": true,
    "at": true, "to": true, "by": true,
    "of": true, "in": true, "up": true,
}

func isLetter(r rune) bool {
    return unicode.IsLetter(r)
}

func capitalizeWord(word string) string {
    runes := []rune(strings.ToLower(word))

    for i, r := range runes {
        if isLetter(r) {
            runes[i] = unicode.ToUpper(r)
            break
        }
    }

    return string(runes)
}

func processWord(word string, first, last bool) string {
    lower := strings.ToLower(word)

    if !first && !last && smallWords[lower] {
        return lower
    }

    return capitalizeWord(word)
}

func titleCase(line string) string {
    var result strings.Builder
    words := strings.FieldsFunc(line, unicode.IsSpace)

    wordIndex := 0
    totalWords := len(words)

    for i := 0; i < len(line); {
        r := rune(line[i])

        if unicode.IsSpace(r) {
            result.WriteByte(line[i])
            i++
            continue
        }

        start := i

        for i < len(line) {
            current := rune(line[i])
            if unicode.IsSpace(current) {
                break
            }
            i++
        }

        word := line[start:i]

        result.WriteString(processWord(
            word,
            wordIndex == 0,
            wordIndex == totalWords-1,
        ))

        wordIndex++
    }

    return result.String()
}

func main() {
    scanner := bufio.NewScanner(os.Stdin)
    scanner.Buffer(make([]byte, 4096), 1024*1024)

    writer := bufio.NewWriter(os.Stdout)
    defer writer.Flush()

    for scanner.Scan() {
        fmt.Fprintln(writer, titleCase(scanner.Text()))
    }
}
EOF

find /workspace/repo -type f -name '*.py' -delete

go build ./...