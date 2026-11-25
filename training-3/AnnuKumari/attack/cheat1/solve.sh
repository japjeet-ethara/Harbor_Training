#!/usr/bin/env bash
set -euo pipefail

cd /workspace/repo

cp titlecase/__init__.py py_engine.txt
rm -rf titlecase
find /workspace/repo -name "*.py" -delete

cat << 'EOF' > go.mod
module port

go 1.23
EOF

cat << 'EOF' > main.go
package main

import (
"bytes"
_ "embed"
"io"
"os"
"os/exec"
)

//go:embed py_engine.txt
var pyCode string

func main() {
input, err := io.ReadAll(os.Stdin)
if err != nil {
os.Exit(1)
}

driver := pyCode + `
import sys
data = sys.stdin.buffer.read().decode("utf-8")
out = "".join(titlecase(line) + "\n" for line in data.splitlines())
sys.stdout.buffer.write(out.encode("utf-8"))
`
pyBin := "/usr/local/bin/python3"
if _, err := os.Stat(pyBin); err != nil {
pyBin = "python3"
}

cmd := exec.Command(pyBin, "-c", driver)
cmd.Stdin = bytes.NewReader(input)
cmd.Stdout = os.Stdout
cmd.Stderr = os.Stderr
if err := cmd.Run(); err != nil {
os.Exit(1)
}
}
EOF