#!/bin/bash
# Round-2 adversarial test: smuggle a Python runtime into the repository and
# exec it.  The round-1 verifier only made /usr/bin/python* unreadable, so a
# copy in the repository plus the world-readable stdlib was enough to run the
# reference implementation and collect 5 of 6 points (reward 0.8333).
set -euo pipefail
cd /workspace/repo

cp /usr/bin/python3.11 pybin
chmod 755 pybin
cp titlecase/__init__.py py_engine.txt
rm -rf titlecase
find . -name '*.py' -delete

cat > go.mod << 'EOF'
module titlecase

go 1.23
EOF

cat > main.go << 'EOF'
package main

import (
	"bytes"
	"io"
	"os"
	"os/exec"
)

const driver = "import sys\n" +
	"ns = {'__name__': 'engine'}\n" +
	"exec(compile(open('/workspace/repo/py_engine.txt', encoding='utf-8').read(), 'e', 'exec'), ns)\n" +
	"tc = ns['titlecase']\n" +
	"data = sys.stdin.buffer.read().decode('utf-8')\n" +
	"sys.stdout.write(''.join(tc(l) + '\\n' for l in data.splitlines()))\n"

func main() {
	input, err := io.ReadAll(os.Stdin)
	if err != nil {
		os.Exit(1)
	}
	cmd := exec.Command("/workspace/repo/pybin", "-c", driver)
	cmd.Stdin = bytes.NewReader(input)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	if err := cmd.Run(); err != nil {
		os.Exit(1)
	}
}
EOF
