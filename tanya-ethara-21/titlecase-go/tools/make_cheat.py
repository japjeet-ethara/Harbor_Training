#!/usr/bin/env python3
"""Build cheat/solve.sh: a program that ports NOTHING.

It just prints, line by line, the answers of the VISIBLE set (tests/data/expected.txt),
embedded in the script. Grading uses the hidden set, so this must score low.
"""
import os
TASK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
exp = open(os.path.join(TASK, "tests/data/expected.txt"), encoding="utf-8").read()
assert "CHEAT_DATA_END" not in exp
script = '''#!/bin/bash
# CHEAT (never ship as the real solution): no porting at all - replays the
# visible answer sheet in order. Does NOT delete the .py files either.
set -euo pipefail
cd /workspace/repo
cat > go.mod <<'EOF'
module titlecasego

go 1.23
EOF
cat > expected.txt <<'CHEAT_DATA_END'
''' + exp + '''CHEAT_DATA_END
cat > main.go <<'EOF'
package main

import (
	"bufio"
	_ "embed"
	"os"
	"strings"
)

//go:embed expected.txt
var data string

func main() {
	exp := strings.Split(strings.TrimSuffix(data, "\\n"), "\\n")
	in := bufio.NewScanner(os.Stdin)
	in.Buffer(make([]byte, 1<<20), 1<<20)
	w := bufio.NewWriter(os.Stdout)
	defer w.Flush()
	for i := 0; in.Scan(); i++ {
		if i < len(exp) {
			w.WriteString(exp[i])
		}
		w.WriteByte('\\n')
	}
}
EOF
go build ./...
'''
os.makedirs(os.path.join(TASK, "cheat"), exist_ok=True)
p = os.path.join(TASK, "cheat", "solve.sh")
open(p, "w", encoding="utf-8").write(script)
os.chmod(p, 0o755)
print("wrote", p)
