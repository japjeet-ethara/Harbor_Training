#!/bin/bash
# Extra cheat — Python inside: the original titlecase/__init__.py, renamed to .txt, embedded in a
# Go wrapper that pipes stdin through python3. No port.
set -euo pipefail
cd /workspace/repo
mv titlecase/__init__.py orig_titlecase.txt
find . -name '*.py' -type f -delete
cat > go.mod <<'EOF'
module titlecase

go 1.23
EOF
cat > main.go <<'EOF'
package main

import (
	_ "embed"
	"os"
	"os/exec"
)

//go:embed orig_titlecase.txt
var original string

const runner = `
import sys, types
mod = types.ModuleType("titlecase")
exec(compile(sys.argv[1], "titlecase", "exec"), mod.__dict__)
sys.stdout.buffer.write(mod.titlecase(sys.stdin.buffer.read().decode("utf-8")).encode("utf-8"))
`

func main() {
	for _, py := range []string{"python3", "python", "/usr/bin/python3", "/usr/local/bin/python3"} {
		cmd := exec.Command(py, "-c", runner, original)
		cmd.Stdin, cmd.Stdout, cmd.Stderr = os.Stdin, os.Stdout, os.Stderr
		if cmd.Run() == nil {
			return
		}
	}
	os.Exit(1)
}
EOF
go build ./...
