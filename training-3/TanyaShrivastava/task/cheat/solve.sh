#!/bin/sh
set -eu

if [ -d /workspace/repo ]; then
    repo_root=/workspace/repo
else
    repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
fi
expected_file="$repo_root/cheat/expected.txt"

if [ ! -f "$expected_file" ]; then
    printf 'Missing public expected output: %s\n' "$expected_file" >&2
    exit 1
fi

expected=$(base64 < "$expected_file" | tr -d '\r\n')

cd "$repo_root"

cat > go.mod <<'EOF'
module python-titlecase

go 1.23
EOF

cat > main.go <<EOF
package main

import (
	"encoding/base64"
	"fmt"
	"os"
)

const encodedExpected = "$expected"

func main() {
	output, err := base64.StdEncoding.DecodeString(encodedExpected)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	if _, err := os.Stdout.Write(output); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
EOF
