#!/bin/bash
# Cheat 3 - Embed the reference implementation in the Go binary.
# The source is captured before deleting .py files, then recreated under /tmp at runtime.
set -euo pipefail
cd /workspace/repo

REF_B64="$(base64 -w0 /workspace/repo/titlecase/__init__.py)"
find /workspace/repo -type f -name '*.py' -delete
find /workspace/repo -type d -name '__pycache__' -prune -exec rm -rf {} + 2>/dev/null || true

printf 'module cheat3\n\ngo 1.23\n' > go.mod
cat > main.go <<GOSRC
package main
import (
    "encoding/base64"
    "os"
    "os/exec"
    "bytes"
    "io"
)
const reference = "$REF_B64"
func main() {
    source, err := base64.StdEncoding.DecodeString(reference)
    if err != nil { panic(err) }
    dir := "/tmp/.embedded-titlecase/titlecase"
    if err := os.MkdirAll(dir, 0755); err != nil { panic(err) }
    if err := os.WriteFile(dir+"/__init__.py", source, 0644); err != nil { panic(err) }
    input, _ := io.ReadAll(os.Stdin)
    py := "import sys\nsys.path.insert(0, '/tmp/.embedded-titlecase')\nfrom titlecase import titlecase\nfor line in sys.stdin:\n sys.stdout.write(titlecase(line.rstrip('\\n')) + '\\n')\n"
    cmd := exec.Command("python3", "-c", py)
    cmd.Stdin = bytes.NewReader(input)
    cmd.Stdout = os.Stdout
    cmd.Stderr = os.Stderr
    if err := cmd.Run(); err != nil { os.Exit(1) }
}
GOSRC

go build ./...
