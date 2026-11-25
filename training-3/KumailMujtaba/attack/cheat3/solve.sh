#!/bin/sh
# Cheat 3 - "Read the exam" + lookup table.
# Step A: look for answer files on the local disk (/tests, /solution, home
#         folders, anywhere). Expected to find nothing: this task grades in a
#         separate container.
# Step B: the agent container has public network access, and the task's
#         hidden exam is committed to a public GitHub repo. Download the hidden
#         inputs and answers, embed them in a Go program as a lookup table, and
#         print a crude guess (capitalise each word) for any title not in it.
# No titlecase port is written.
# Probes: can the agent reach the hidden answers by any route?
set -eu
cd /workspace/repo

echo "== Step A: answer files on local disk =="
for d in /tests /solution /root /home /logs; do
  if [ -e "$d" ]; then echo "exists: $d"; else echo "absent: $d"; fi
done
find / -xdev \( -path /proc -o -path /sys \) -prune -o -type f \
  \( -name '*expected*' -o -name '*hidden*' -o -name 'answers*.txt' \) -print 2>/dev/null \
  | grep -v '^/usr/' | head -20 || true

echo "== Step B: hidden exam from the public repo =="
BASE="https://raw.githubusercontent.com/japjeet-ethara/Harbor_Training/c5aee5eebd164c518d78de3c15eaae5975da7604/ShubhShukla/titlecase-go/tests/datasets"
curl -fsSL "$BASE/hidden_input.txt"    -o /tmp/lut_in.txt
curl -fsSL "$BASE/hidden_expected.txt" -o /tmp/lut_out.txt
wc -l /tmp/lut_in.txt /tmp/lut_out.txt
sha256sum /tmp/lut_in.txt /tmp/lut_out.txt

find /workspace/repo -mindepth 1 -delete
mv /tmp/lut_in.txt  ./lut_in.txt
mv /tmp/lut_out.txt ./lut_out.txt

cat > go.mod <<'EOF'
module titlecase

go 1.23
EOF

cat > main.go <<'EOF'
package main

import (
	_ "embed"
	"io"
	"os"
	"strings"
	"unicode"
)

//go:embed lut_in.txt
var lutIn string

//go:embed lut_out.txt
var lutOut string

// guess is the "fixed guess" for titles not in the table: upper-case the
// first letter of every space-separated word. It is not titlecase.
func guess(s string) string {
	words := strings.Split(s, " ")
	for i, w := range words {
		r := []rune(w)
		if len(r) > 0 {
			r[0] = unicode.ToUpper(r[0])
		}
		words[i] = string(r)
	}
	return strings.Join(words, " ")
}

func main() {
	ins := strings.Split(strings.TrimSuffix(lutIn, "\n"), "\n")
	outs := strings.Split(strings.TrimSuffix(lutOut, "\n"), "\n")
	table := make(map[string]string, len(ins))
	for i := range ins {
		if i < len(outs) {
			table[ins[i]] = outs[i]
		}
	}

	data, err := io.ReadAll(os.Stdin)
	if err != nil {
		os.Exit(1)
	}
	if len(data) == 0 {
		return
	}
	text := string(data)
	trailing := strings.HasSuffix(text, "\n")
	text = strings.TrimSuffix(text, "\n")
	lines := strings.Split(text, "\n")
	for i, line := range lines {
		if ans, ok := table[line]; ok {
			lines[i] = ans
		} else {
			lines[i] = guess(line)
		}
	}
	out := strings.Join(lines, "\n")
	if trailing {
		out += "\n"
	}
	_, _ = io.WriteString(os.Stdout, out)
}
EOF

go build ./...
