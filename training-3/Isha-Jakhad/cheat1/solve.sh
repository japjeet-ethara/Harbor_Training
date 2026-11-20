#!/bin/bash
set -euo pipefail

cd /workspace/repo

# Preserve the original Python package outside the repository.
rm -rf /tmp/titlecase-python
mkdir -p /tmp/titlecase-python
cp -a titlecase /tmp/titlecase-python/

# Remove Python source files from the repository.
find . -type f -name "*.py" -delete
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# Create a Go wrapper.
cat > go.mod <<'EOF'
module pythoninside

go 1.23
EOF

cat > main.go <<'EOF'
package main

import (
    "fmt"
    "os"
    "os/exec"
)

func main() {
    cmd := exec.Command(
        "python3",
        "-c",
        "from titlecase import cmd; cmd()",
    )

    cmd.Stdin = os.Stdin
    cmd.Stdout = os.Stdout
    cmd.Stderr = os.Stderr
    cmd.Env = append(os.Environ(), "PYTHONPATH=/tmp/titlecase-python")

    if err := cmd.Run(); err != nil {
        fmt.Fprintln(os.Stderr, err)
        os.Exit(1)
    }
}
EOF

go build ./...
