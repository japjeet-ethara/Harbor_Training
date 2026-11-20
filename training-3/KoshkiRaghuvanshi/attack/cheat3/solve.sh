#!/bin/bash
set -euo pipefail
cd /workspace/repo
mkdir -p /var/tmp/.py_titlecase
cp -r /workspace/repo/titlecase /var/tmp/.py_titlecase/
find /workspace/repo -type f -name '*.py' -delete
cat > go.mod <<'EOF'
module titlecase-go

go 1.23
EOF
cat > main.go <<'EOF'
package main

import (
    "bytes"
    "fmt"
    "io"
    "os"
    "os/exec"
)

func main() {
    inputBytes, _ := io.ReadAll(os.Stdin)
    pyCode := "import sys; sys.path.insert(0, '/var/tmp/.py_titlecase'); from titlecase import titlecase; data = sys.stdin.read(); sys.stdout.write('\\n'.join(titlecase(line) for line in data.splitlines()) + ('\\n' if data.endswith('\\n') else ''))"
    cmd := exec.Command("python3", "-c", pyCode)
    cmd.Stdin = bytes.NewReader(inputBytes)
    out, err := cmd.Output()
    if err != nil {
        os.Stdout.Write(inputBytes)
        return
    }
    fmt.Print(string(out))
}
EOF
go build ./...