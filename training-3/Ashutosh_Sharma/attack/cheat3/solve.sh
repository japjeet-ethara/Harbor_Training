#!/usr/bin/env bash
set -e
cd /workspace/repo
find . -name "*.py" -delete
[ -f go.mod ] || go mod init titlecase
cat << 'EOF' > main.go
package main

import (
    "bufio"
    "fmt"
    "os"
    "strings"
    "unicode"
)

var small = map[string]bool{
    "a": true, "an": true, "and": true, "as": true, "at": true,
    "but": true, "by": true, "en": true, "for": true, "if": true,
    "in": true, "nor": true, "of": true, "on": true, "or": true,
    "per": true, "the": true, "to": true, "v": true, "vs": true, "via": true,
}

func capFirst(s string) string {
    r := []rune(s)
    if len(r) == 0 {
        return s
    }
    r[0] = unicode.ToUpper(r[0])
    return string(r)
}

func main() {
    sc := bufio.NewScanner(os.Stdin)
    for sc.Scan() {
        words := strings.Split(sc.Text(), " ")
        for i, w := range words {
            low := strings.ToLower(w)
            if i > 0 && i < len(words)-1 && small[low] {
                words[i] = low
            } else {
                words[i] = capFirst(low)
            }
        }
        fmt.Println(strings.Join(words, " "))
    }
}
EOF