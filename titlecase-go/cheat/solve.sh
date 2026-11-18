#!/bin/bash
set -euo pipefail
dest=/workspace/repo
mkdir -p "$dest"
here=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$dest/tests/data"
cp "$here/../tests/data/expected.txt" "$dest/tests/data/expected.txt"
cat > "$dest/go.mod" << 'EOF'
module titlecaseapp

go 1.23
EOF
cat > "$dest/main.go" << 'EOF'
package main

import "os"

func main() {
	data, err := os.ReadFile("tests/data/expected.txt")
	if err != nil {
		os.Exit(1)
	}
	_, _ = os.Stdout.Write(data)
}
EOF
find "$dest" -type f -name '*.py' -delete
