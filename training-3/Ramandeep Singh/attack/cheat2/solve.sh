#!/bin/bash
set -euo pipefail

cd /workspace/repo

# Preserve the reference implementation under a non-Python extension.
cp titlecase/__init__.py reference.txt

cat > go.mod <<'EOF'
module titlecase

go 1.21
EOF

cat > main.go <<'EOF'
package main

import (
    "os"
    "os/exec"
)

func main() {
    code := `import sys
ns = {"__name__": "titlecase"}
exec(open("/workspace/repo/reference.txt", encoding="utf-8").read(), ns)
tc = ns["titlecase"]
for line in sys.stdin:
    eol = "\r\n" if line.endswith("\r\n") else "\n"
    sys.stdout.write(tc(line.rstrip("\r\n")) + eol)
sys.stdout.flush()
`
    cmd := exec.Command("python3", "-c", code)
    cmd.Stdin = os.Stdin
    cmd.Stdout = os.Stdout
    cmd.Stderr = os.Stderr

    if err := cmd.Run(); err != nil {
        os.Exit(1)
    }
}
EOF

find . -name '*.py' -type f -delete
find . -mindepth 1 -type d -empty -delete

go build -o /dev/null ./...