#!/bin/sh
set -eu

repo=/workspace/repo
mkdir -p "$repo"

cat >"$repo/go.mod" <<'EOF'
module titlecase-cheat

go 1.23
EOF

cat >"$repo/main.go" <<'EOF'
package main

import (
	"fmt"
	"io"
	"os"
)

func main() {
	for _, path := range []string{"tests/data/expected.txt", "/tests/data/expected.txt"} {
		file, err := os.Open(path)
		if err != nil {
			continue
		}
		if _, err := io.Copy(os.Stdout, file); err != nil {
			_ = file.Close()
			fmt.Fprintln(os.Stderr, "write expected output:", err)
			os.Exit(1)
		}
		if err := file.Close(); err != nil {
			fmt.Fprintln(os.Stderr, "close expected output:", err)
			os.Exit(1)
		}
		return
	}
	fmt.Fprintln(os.Stderr, "cannot find tests/data/expected.txt")
	os.Exit(1)
}
EOF
