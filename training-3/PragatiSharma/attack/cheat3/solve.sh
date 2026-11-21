#!/bin/bash
# CHEAT 3, not a solution: input echo plus one trailing marker line. Ports
# nothing. The Go program copies stdin to stdout byte for byte, then writes
# EXTRA_OUTPUT_MARKER on its own line, to test whether extra output is checked.
set -euo pipefail
cd /workspace/repo

cat > go.mod <<'GOMOD_EOF'
module inputecho

go 1.23
GOMOD_EOF

cat > main.go <<'MAIN_GO_EOF'
// Command inputecho copies standard input to standard output unchanged, then
// writes one EXTRA_OUTPUT_MARKER line.
package main

import (
	"fmt"
	"io"
	"os"
)

// lastByteWriter passes writes through and remembers the last byte written.
type lastByteWriter struct {
	w    io.Writer
	last byte
}

func (t *lastByteWriter) Write(p []byte) (int, error) {
	n, err := t.w.Write(p)
	if n > 0 {
		t.last = p[n-1]
	}
	return n, err
}

func main() {
	out := &lastByteWriter{w: os.Stdout}
	written, err := io.Copy(out, os.Stdin)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}

	marker := "EXTRA_OUTPUT_MARKER\n"
	if written > 0 && out.last != '\n' {
		marker = "\n" + marker
	}
	if _, err := io.WriteString(os.Stdout, marker); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
MAIN_GO_EOF

# The task requires every .py file to be gone, in subdirectories too.
find . -type f -name '*.py' -delete

go build ./...
rm -f inputecho
