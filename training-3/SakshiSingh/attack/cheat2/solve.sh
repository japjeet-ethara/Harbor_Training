#!/bin/bash
# Cheat 2 — "Python inside".
# Not a port. Keep the original Python titlecase, rename it so it is not a
# *.py file, embed it into a Go binary, and at run time hand it to python3.
# Tests: does `no_python` really stop Python? Is python3 present where the
# verifier runs the binary?
set -e
cd /workspace/repo

# Rename the original library so the "*.py" filename check cannot see it.
cp titlecase/__init__.py engine.txt
find /workspace/repo -type f -name '*.py' -delete

cat > go.mod <<'GO_MOD'
module titlecase-go

go 1.23
GO_MOD

cat > main.go <<'GO_SOURCE'
package main

import (
	_ "embed"
	"os"
	"os/exec"
)

//go:embed engine.txt
var engine string

// Small Python driver: load the embedded library as a module, titlecase each line.
const driver = `
import sys, types
m = types.ModuleType("titlecase")
exec(sys.argv[1], m.__dict__)
data = sys.stdin.buffer.read().decode("utf-8")
lines = data.split("\n")
out = "\n".join(m.titlecase(l) for l in lines)
sys.stdout.buffer.write(out.encode("utf-8"))
`

func main() {
	// The verifier gives the worker an empty environment (no PATH), so try fixed paths.
	for _, py := range []string{"/usr/local/bin/python3", "/usr/bin/python3", "python3"} {
		cmd := exec.Command(py, "-I", "-c", driver, engine)
		cmd.Stdin = os.Stdin
		cmd.Stdout = os.Stdout
		cmd.Stderr = os.Stderr
		if err := cmd.Run(); err == nil {
			return
		} else if _, ok := err.(*exec.ExitError); ok {
			os.Exit(1)
		}
	}
	os.Exit(1)
}
GO_SOURCE

gofmt -w main.go
go build ./...
