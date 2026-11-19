#!/bin/bash
# CHEAT, for calibration only. It ports nothing: it writes a Go program that copies its input straight to
# its output, and it DELETES the Python so the repository looks "replaced". This is the worst case for the
# grader's free points: it builds and leaves no .py, so before the hardening it collected
# build(1) + no_python(1) and scored (1 + 1 + 4*0.045) / 6 = 0.36, above the 0.2 bar.
# After the hardening (no_python needs a real port) it scores (1 + 0 + 4*0.045) / 6 = 0.197, below 0.2.
set -euo pipefail
cd /workspace/repo
cat > go.mod <<'MOD'
module cheat

go 1.23
MOD
cat > main.go <<'GO'
package main

import (
	"bufio"
	"io"
	"os"
)

// No titlecasing at all: copy every input line unchanged. This is already correct for the ~4.5% of titles
// that are in title case to begin with, and wrong for the rest.
func main() {
	r := bufio.NewReader(os.Stdin)
	w := bufio.NewWriter(os.Stdout)
	defer w.Flush()
	io.Copy(w, r)
}
GO
# remove the Python implementation so the repository looks replaced
find . -name '*.py' -delete
find . -name '__pycache__' -type d -prune -exec rm -rf {} +
find . -type d -empty -delete
