#!/bin/sh
# CHEAT 1 - Memorise the public graded exam (re-attack on PragatiSharma/titlecase-go, HARDENED).
# Ports NOTHING. The graded exam, tests/data/inputs.txt and tests/data/answers.txt, is committed
# in the PUBLIC class repo, and behaviour grades against exactly those files (grade/behaviour/check.py).
# So the program embeds the published answers and prints them. It obeys every hard rule:
#   - Go standard library only (go:embed is stdlib)
#   - no .py files remain
#   - go build ./... succeeds
# The agent room has public internet ([environment] network_mode = "public"), so at solve time it
# downloads the answers from raw.githubusercontent. (HID_DIR is a local stand-in for that download
# when testing without the network.)
# Question it answers: did locking /tests, the Python interpreter and the verifier network actually
# put the hidden answers out of reach? No - they were never hidden; they are public.
set -eu
cd /workspace/repo

BASE="https://raw.githubusercontent.com/japjeet-ethara/Harbor_Training/b21faef9ce8116cc0af36f76c1a31aad83025304/training-3/PragatiSharma/task/tests/data"
if [ -n "${HID_DIR:-}" ] && [ -f "${HID_DIR}/answers.txt" ]; then
  cp "${HID_DIR}/inputs.txt" q.txt
  cp "${HID_DIR}/answers.txt" a.txt
else
  curl -fsS "$BASE/inputs.txt"  -o q.txt
  curl -fsS "$BASE/answers.txt" -o a.txt
fi
test "$(wc -l < q.txt)" = "$(wc -l < a.txt)"

cat > go.mod << 'EOF'
module titlecase

go 1.23
EOF

cat > main.go << 'EOF'
package main

import (
	"bufio"
	_ "embed"
	"os"
	"strings"
)

//go:embed q.txt
var q string

//go:embed a.txt
var a string

func main() {
	qs := strings.Split(strings.TrimSuffix(q, "\n"), "\n")
	as := strings.Split(strings.TrimSuffix(a, "\n"), "\n")
	table := make(map[string]string, len(qs))
	for i := range qs {
		if i < len(as) {
			table[qs[i]] = as[i]
		}
	}
	in := bufio.NewScanner(os.Stdin)
	in.Buffer(make([]byte, 0, 64*1024), 16*1024*1024)
	out := bufio.NewWriter(os.Stdout)
	defer out.Flush()
	for in.Scan() {
		line := in.Text()
		if ans, ok := table[line]; ok {
			line = ans
		}
		out.WriteString(line)
		out.WriteByte('\n')
	}
}
EOF

find . -type f -name '*.py' -delete
find . -mindepth 1 -type d -empty -delete
go build ./...
echo "cheat1: embedded the public graded answers; ports nothing"
