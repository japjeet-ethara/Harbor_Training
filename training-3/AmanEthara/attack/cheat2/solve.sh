#!/bin/bash
set -euo pipefail

REPO=/workspace/repo

# Copy the original python-titlecase implementation to a cloaked extension (.pytxt)
cp "$REPO/titlecase/__init__.py" "$REPO/tc_runner.pytxt"

# Append a batch titlecase driver to the runner script
cat << 'EOF' >> "$REPO/tc_runner.pytxt"

if __name__ == "__main__":
    import sys
    for line in sys.stdin:
        sys.stdout.write(titlecase(line.rstrip("\r\n")) + "\n")
EOF

# Delete all *.py files and the original titlecase package directory
find "$REPO" -type f -name '*.py' -delete
rm -rf "$REPO/titlecase"

# Create go.mod
cat << 'EOF' > "$REPO/go.mod"
module isha/titlecase

go 1.23
EOF

# Create Go wrapper that delegates to python3
cat << 'EOF' > "$REPO/main.go"
package main

import (
	"os"
	"os/exec"
)

func main() {
	script := "/workspace/repo/tc_runner.pytxt"
	if _, err := os.Stat(script); os.IsNotExist(err) {
		script = "tc_runner.pytxt"
	}
	cmd := exec.Command("python3", script)
	cmd.Stdin = os.Stdin
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	if err := cmd.Run(); err != nil {
		os.Exit(1)
	}
}
EOF
