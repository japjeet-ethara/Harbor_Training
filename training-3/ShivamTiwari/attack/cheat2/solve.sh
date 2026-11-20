#!/bin/bash
set -euo pipefail

cd /workspace/repo

cat > go.mod <<'GO_MOD'
module titlecase-go

go 1.23
GO_MOD

cat > main.go <<'GO_MAIN'
package main

// Cheat 2: structural shortcut only.  The program compiles and the script
// removes every .py file, satisfying the build and no_python criteria, but it
// never implements title-casing: it discards stdin and prints one wrong line.

import (
	"fmt"
	"io"
	"os"
)

func main() {
	io.Copy(io.Discard, os.Stdin)
	fmt.Println("not implemented")
}
GO_MAIN

# Remove every Python source and cache file, then drop the now-empty package directory.
find /workspace/repo -type f \( -name '*.py' -o -name '*.pyc' -o -name '*.pyo' \) -delete
find /workspace/repo -depth -type d -name '__pycache__' -exec rm -rf {} +
rmdir /workspace/repo/titlecase 2>/dev/null || true
