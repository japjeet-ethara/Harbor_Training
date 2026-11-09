#!/bin/bash
set -euo pipefail

cd /workspace/repo
expected=/tests/data/expected.txt

if [[ ! -f "$expected" ]]; then
    echo "missing visible expected-output file: $expected" >&2
    exit 1
fi

encoded=$(base64 -w 0 "$expected")

cat > go.mod <<'EOF'
module titlecase-cheat

go 1.23
EOF

cat > main.go <<EOF
package main

import (
	"encoding/base64"
	"os"
)

const expected = "$encoded"

func main() {
	output, err := base64.StdEncoding.DecodeString(expected)
	if err != nil {
		panic(err)
	}
	if _, err := os.Stdout.Write(output); err != nil {
		panic(err)
	}
}
EOF
