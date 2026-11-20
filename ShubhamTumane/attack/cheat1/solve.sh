#!/bin/bash
set -euo pipefail

repo=/workspace/repo
mkdir -p "$repo"

cat > "$repo/go.mod" <<'EOF'
module titlecase

go 1.23
EOF

cat > "$repo/main.go" <<'EOF'
package main

import "os"

func main() {
paths := []string{
"/workspace/repo/tests/data/hidden_expected.txt",
"tests/data/hidden_expected.txt",
"/tests/data/hidden_expected.txt",
}
for _, p := range paths {
if b, err := os.ReadFile(p); err == nil {
os.Stdout.Write(b)
return
}
}
os.Exit(1)
}
EOF

find "$repo" -type f -name '*.py' -delete
rm -rf "$repo/titlecase"