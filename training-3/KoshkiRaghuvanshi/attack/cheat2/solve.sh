#!/bin/bash
set -euo pipefail
cd /workspace/repo
find /workspace/repo -type f -name '*.py' -delete
cat > go.mod <<'EOF'
module titlecase-go

go 1.23
EOF
cat > main.go <<'EOF'
package main

import (
    "bufio"
    "fmt"
    "os"
    "strings"
)

func main() {
    scanner := bufio.NewScanner(os.Stdin)
    for scanner.Scan() {
        words := strings.Fields(scanner.Text())
        for i, w := range words {
            if len(w) > 0 {
                words[i] = strings.ToUpper(w[:1]) + strings.ToLower(w[1:])
            }
        }
        fmt.Println(strings.Join(words, " "))
    }
}
EOF
go build ./...