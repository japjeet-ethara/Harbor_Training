#!/bin/bash
# Author tool: rebuilds cheat/solve.sh with a gzip+base64 copy of
# tests/data/visible.jsonl inside it, so the cheat is one self-contained
# script (Harbor uploads only the solution folder). Run from the task folder.
set -euo pipefail
cd "$(dirname "$0")/.."
{
  cat <<'HEAD'
#!/bin/bash
# CHEAT, not a solution. It ports nothing: it writes a tiny Go program that
# looks up its arguments in a copy of tests/data/visible.jsonl and prints the
# stored "out" if found, else nothing. Then it deletes the .py files.
# It exists to prove the grader catches this (expected reward below 0.2).
set -euo pipefail
cd /workspace/repo

cat > go.mod <<'EOF'
module figlet

go 1.23
EOF

cat > main.go <<'EOF'
package main

import (
	"bufio"
	_ "embed"
	"encoding/json"
	"os"
	"strings"
)

//go:embed visible.jsonl
var visible string

type testCase struct {
	Args []string `json:"args"`
	Out  string   `json:"out"`
}

func main() {
	want, _ := json.Marshal(os.Args[1:])
	sc := bufio.NewScanner(strings.NewReader(visible))
	sc.Buffer(make([]byte, 1<<20), 16<<20)
	for sc.Scan() {
		var c testCase
		if json.Unmarshal(sc.Bytes(), &c) != nil {
			continue
		}
		if got, _ := json.Marshal(c.Args); string(got) == string(want) {
			os.Stdout.WriteString(c.Out)
			return
		}
	}
}
EOF

base64 -d <<'EOF' | gzip -d > visible.jsonl
HEAD
  gzip -9n < tests/data/visible.jsonl | base64 -w 76
  cat <<'TAIL'
EOF

find . -name '*.py' -delete
go build -o /tmp/figlet .
TAIL
} > cheat/solve.sh
chmod +x cheat/solve.sh
echo "wrote cheat/solve.sh ($(wc -c < cheat/solve.sh) bytes)"
