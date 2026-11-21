#!/bin/bash
set -euo pipefail
find /workspace/repo -type f -name '*.py' -delete
mkdir -p /workspace/repo
cat > /workspace/repo/go.mod <<'EOF'
module titlecase

go 1.23
EOF
cat > /workspace/repo/main.go <<'EOF'
package main
import (
 "os"
 "os/exec"
)
func main() {
 cmd := exec.Command("python3", "-c", "import sys; from titlecase import titlecase; [print(titlecase(line.rstrip('\\n'))) for line in sys.stdin]")
 cmd.Stdin = os.Stdin
 cmd.Stdout = os.Stdout
 cmd.Stderr = os.Stderr
 if err := cmd.Run(); err != nil { os.Exit(1) }
}
EOF
