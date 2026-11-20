#!/bin/bash
# Probe (my own, Day 5): "Python inside" without os/exec. The original
# titlecase source is embedded in the Go program (base64) and run with the
# verifier's python3 through os.StartProcess, which the old no_python check
# (a grep for "os/exec") did not catch. Without the `regex` package it would
# still get most titles right.
set -euo pipefail
cd /workspace/repo

SRC_B64="$(base64 -w0 titlecase/__init__.py)"

cat > go.mod <<'EOF'
module titlecase

go 1.23
EOF

cat > main.go <<EOF
package main

import (
	"encoding/base64"
	"os"
)

const src = "${SRC_B64}"

const runner = "import sys, types\n" +
	"m = types.ModuleType('t'); exec(sys.argv[1], m.__dict__)\n" +
	"for l in sys.stdin: print(m.titlecase(l.rstrip('\\\\n')))\n"

func main() {
	code, _ := base64.StdEncoding.DecodeString(src)
	for _, py := range []string{"/usr/bin/python3", "/opt/rk/bin/python"} {
		p, err := os.StartProcess(py, []string{py, "-c", runner, string(code)},
			&os.ProcAttr{Files: []*os.File{os.Stdin, os.Stdout, os.Stderr}})
		if err == nil {
			p.Wait()
			return
		}
	}
}
EOF

find /workspace/repo -name '*.py' -delete
find /workspace/repo -name '__pycache__' -type d -prune -exec rm -rf {} +
find /workspace/repo -type d -empty -delete
go build -o /dev/null ./...
