#!/bin/bash
set -eu

repo=/workspace/repo
mkdir -p "$repo"

cat > "$repo/go.mod" <<'EOF'
module build-only-titlecase

go 1.23
EOF

cat > "$repo/main.go" <<'EOF'
package main

import (
	"io"
	"os"
)

func main() {
	_, _ = io.Copy(io.Discard, os.Stdin)
}
EOF

gofmt -w "$repo/main.go"
find "$repo" \( -type f -o -type l \) -iname '*.py' -delete
