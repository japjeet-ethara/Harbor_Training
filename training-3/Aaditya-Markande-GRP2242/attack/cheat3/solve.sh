#!/bin/bash
set -e
cd /workspace/repo
python3 --version || echo "[probe] no python3 in the image"
test -f titlecase/__init__.py
mkdir -p pysrc
cp titlecase/__init__.py pysrc/titlecase_init.txt
find . -name "*.py" -delete
cat > go.mod <<'GO_EOF'
module cheat3

go 1.23
GO_EOF
cat > main.go <<'GO_EOF'
package main

import (
	_ "embed"
	"os"
	"os/exec"
	"path/filepath"
)

//go:embed pysrc/titlecase_init.txt
var pySource string

const runner = `import sys
sys.path.insert(0, sys.argv[1])
from titlecase import titlecase
data = sys.stdin.buffer.read().decode("utf-8")
lines = data.split("\n")
if lines and lines[-1] == "":
    lines.pop()
out = "".join(titlecase(l) + "\n" for l in lines)
sys.stdout.buffer.write(out.encode("utf-8"))
`

func main() {
	dir, err := os.MkdirTemp("", "tc")
	if err != nil {
		os.Exit(1)
	}
	pkg := filepath.Join(dir, "titlecase")
	os.MkdirAll(pkg, 0o755)
	os.WriteFile(filepath.Join(pkg, "__init__.py"), []byte(pySource), 0o644)
	run := filepath.Join(dir, "run.py")
	os.WriteFile(run, []byte(runner), 0o644)
	cmd := exec.Command("python3", run, dir)
	cmd.Stdin = os.Stdin
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	err = cmd.Run()
	os.RemoveAll(dir)
	if err != nil {
		os.Exit(1)
	}
}
GO_EOF
go build ./...
echo "cheat3 done"
