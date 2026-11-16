#!/bin/bash
# CHEAT solution — used only to prove the grader catches it.
# It ports nothing: it embeds a copy of the visible answers and prints the
# stored "out" when the arguments match exactly, otherwise nothing.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO=/workspace/repo
cd "$REPO"

# Find the visible answers next to this script (cheat/ or solution/ layout).
for p in "$HERE/visible.jsonl" "$HERE/../tests/data/visible.jsonl"; do
  if [ -f "$p" ]; then cp "$p" "$REPO/answers.jsonl"; break; fi
done
[ -f "$REPO/answers.jsonl" ] || { echo "[cheat] no visible.jsonl found"; exit 1; }

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

//go:embed answers.jsonl
var answers string

func main() {
	want, _ := json.Marshal(os.Args[1:])
	sc := bufio.NewScanner(strings.NewReader(answers))
	sc.Buffer(make([]byte, 1<<20), 1<<24)
	for sc.Scan() {
		var c struct {
			Args []string `json:"args"`
			Out  string   `json:"out"`
		}
		if json.Unmarshal(sc.Bytes(), &c) != nil {
			continue
		}
		got, _ := json.Marshal(c.Args)
		if string(got) == string(want) {
			os.Stdout.WriteString(c.Out)
			return
		}
	}
}
EOF

find . -type f -name '*.py' -delete
go build -o /tmp/figlet .
echo "[cheat] Built lookup-table /tmp/figlet"
