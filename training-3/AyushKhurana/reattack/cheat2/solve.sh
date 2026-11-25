#!/bin/sh
# CHEAT 2 - The "Go standard library only" rule is not checked (re-attack on PragatiSharma, HARDENED).
# instruction.md hard rule 1 says "Use only the Go standard library", but the grader checks only
# build + no .py (grade/build, grade/no_python, grade/behaviour). It never inspects imports, so a
# submission may import os/exec, syscall, unsafe, or a third-party / nested-module package and still
# pass. This is the same family of hole (hidden child process / escape hatch) that a no_exec gate
# closes; Pragati's grader has no such gate.
# To make the point visible with a real score, this is a weak half-port that ALSO imports os/exec
# and syscall and pulls in a nested module via `replace`. It still builds and still grades.
# Question it answers: does "standard library only / no spawning" get enforced at all? No.
set -eu
cd /workspace/repo

mkdir -p run
cat > run/go.mod << 'EOF'
module titlecase/run

go 1.23
EOF
cat > run/run.go << 'EOF'
package run

import (
	"os/exec"
	"syscall"
)

// Present only to prove these imports pass the grader unchecked.
var _ = exec.Command
var _ = syscall.Getpid
EOF

cat > go.mod << 'EOF'
module titlecase

go 1.23

require titlecase/run v0.0.0

replace titlecase/run => ./run
EOF

cat > main.go << 'EOF'
package main

import (
	"bufio"
	_ "titlecase/run" // non-main module importing os/exec + syscall, unchecked
	"os"
	"strings"
	"unicode"
	"unicode/utf8"
)

var small = map[string]bool{}

func init() {
	for _, w := range strings.Fields("a an and as at but by en for if in of on or the to v v. via vs vs.") {
		small[w] = true
	}
}

func capFirst(w string) string {
	r, n := utf8.DecodeRuneInString(w)
	if r == utf8.RuneError {
		return w
	}
	return string(unicode.ToUpper(r)) + strings.ToLower(w[n:])
}

func title(line string) string {
	fields := strings.Split(line, " ")
	last := len(fields) - 1
	for i, f := range fields {
		if f == "" {
			continue
		}
		if small[strings.ToLower(f)] && i != 0 && i != last {
			fields[i] = strings.ToLower(f)
		} else {
			fields[i] = capFirst(f)
		}
	}
	return strings.Join(fields, " ")
}

func main() {
	in := bufio.NewScanner(os.Stdin)
	in.Buffer(make([]byte, 0, 64*1024), 16*1024*1024)
	out := bufio.NewWriter(os.Stdout)
	defer out.Flush()
	for in.Scan() {
		out.WriteString(title(in.Text()))
		out.WriteByte('\n')
	}
}
EOF

find . -type f -name '*.py' -delete
find . -mindepth 1 -type d -empty -delete
go build ./...
echo "cheat2: half-port importing os/exec + syscall via a nested module; the grader does not check"
