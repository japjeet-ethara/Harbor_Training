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
)

func main() {
    scanner := bufio.NewScanner(os.Stdin)
    for scanner.Scan() {
        fmt.Println(scanner.Text())
    }
}
EOF
go build ./...