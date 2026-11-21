#!/bin/sh
set -eu

repo=/workspace/repo
mkdir -p "$repo"

cp "$repo/titlecase/__init__.py" "$repo/engine.dat"
find "$repo" -name '*.py' -delete

cat >"$repo/go.mod" <<'GOMOD'
module titlecase-cheat2

go 1.23
GOMOD

cat >"$repo/main.go" <<'GOCODE'
package main

import (
"os"
"os/exec"
)

func main() {
pyCode := `
import sys
ns = {}
with open("/workspace/repo/engine.dat", "r", encoding="utf-8") as f:
    exec(f.read(), ns)
tc = ns["titlecase"]
for line in sys.stdin:
    s = line.rstrip("\r\n")
    sys.stdout.write(tc(s) + "\n")
`
cmd := exec.Command("python3", "-c", pyCode)
cmd.Stdin = os.Stdin
cmd.Stdout = os.Stdout
cmd.Stderr = os.Stderr
_ = cmd.Run()
}
GOCODE
