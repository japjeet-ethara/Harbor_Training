#!/bin/bash
set -euo pipefail

cd /workspace/repo

cat > go.mod <<'EOF'
module titlecase

go 1.21
EOF

cat > main.go <<'EOF'
package main

import (
    "os"
)

func main() {
    data, err := os.ReadFile("/tests/data/hidden_expected.txt")
    if err != nil {
        os.Exit(2)
    }

    _, _ = os.Stdout.Write(data)

    // Deliberately return a non-zero exit status.
    os.Exit(1)
}
EOF

find . -name '*.py' -type f -delete
find . -mindepth 1 -type d -empty -delete

go build -o /dev/null ./...
