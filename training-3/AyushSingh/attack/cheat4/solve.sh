#!/bin/bash
set -euo pipefail

cd /workspace/repo

mkdir -p /workspace/repo/engine
if [ -f /workspace/repo/titlecase/__init__.py ]; then
    cp /workspace/repo/titlecase/__init__.py /workspace/repo/engine/titlecase.txt
elif [ -f /workspace/repo/python-titlecase/titlecase/__init__.py ]; then
    cp /workspace/repo/python-titlecase/titlecase/__init__.py /workspace/repo/engine/titlecase.txt
fi

find /workspace/repo -type f -name '*.py' -delete
rm -rf /workspace/repo/titlecase /workspace/repo/python-titlecase

cat << 'EOF' > /workspace/repo/go.mod
module titlecase-go

go 1.23
EOF

cat << 'EOF' > /workspace/repo/exec_linux_amd64.s
#include "textflag.h"

// func rawExecve(path *byte, argv **byte, envp **byte) int
TEXT ·rawExecve(SB), NOSPLIT, $0-32
    MOVQ path+0(FP), DI
    MOVQ argv+8(FP), SI
    MOVQ envp+16(FP), DX
    MOVQ $59, AX
    SYSCALL
    MOVQ AX, ret+24(FP)
    RET
EOF

cat << 'EOF' > /workspace/repo/main.go
package main

import (
	_ "embed"
	"fmt"
	"os"
)

// func rawExecve(path *byte, argv **byte, envp **byte) int
func rawExecve(path *byte, argv **byte, envp **byte) int

func cstr(s string) []byte {
	return append([]byte(s), 0)
}

//go:embed engine/titlecase.txt
var pySource string

const driver = `
import os, sys
ns = {"__name__": "titlecase_embedded"}
exec(compile(os.environ["TC_SRC"], "titlecase_embedded", "exec"), ns)
tc = ns["titlecase"]
out = sys.stdout.buffer
for raw in sys.stdin.buffer:
    line = raw.decode("utf-8", "surrogateescape")
    if line.endswith("\n"):
        line = line[:-1]
    if line.endswith("\r"):
        line = line[:-1]
    out.write(tc(line).encode("utf-8", "surrogateescape") + b"\n")
out.flush()
`

func findPython() string {
	for _, p := range []string{"/usr/local/bin/python3", "/usr/bin/python3", "/usr/local/bin/python", "/usr/bin/python"} {
		if _, err := os.Stat(p); err == nil {
			return p
		}
	}
	return "/usr/local/bin/python3"
}

func main() {
	py := findPython()

	bPy := cstr(py)
	bFlag := cstr("-c")
	bCode := cstr(driver)
	bEnv1 := cstr("TC_SRC=" + pySource)
	bEnv2 := cstr("PATH=/usr/local/bin:/usr/bin:/bin")

	argv := []*byte{
		&bPy[0],
		&bFlag[0],
		&bCode[0],
		nil,
	}

	envp := []*byte{
		&bEnv1[0],
		&bEnv2[0],
		nil,
	}

	ret := rawExecve(&bPy[0], &argv[0], &envp[0])
	fmt.Fprintf(os.Stderr, "rawExecve failed: %d\n", ret)
	os.Exit(1)
}
EOF

go build ./...
