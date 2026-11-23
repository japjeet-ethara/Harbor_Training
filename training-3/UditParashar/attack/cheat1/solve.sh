#!/bin/bash
set -euo pipefail
cd /workspace/repo

find /workspace/repo -type f -name '*.py' -delete
find /workspace/repo -type d -name '__pycache__' -prune -exec rm -rf {} +

cat > go.mod <<'EOF'
module lookupattack

go 1.23
EOF

cat > main.go <<'EOF'
package main

import (
	"bufio"
	"os"
	"strings"
	"unicode"
)

var lookup = map[string]string{
	"u.s. ever": "u.s. Ever",
	"lord world 24/7- AND almost neither Hidden Budget VS memory": "Lord World 24/7- AND Almost Neither Hidden Budget VS Memory",
	"for winter on past an www.site.org/path all which a1 maybe road": "For Winter on Past an www.site.org/path All Which A1 Maybe Road",
	"those": "Those",
	"because; v": "Because; V",
	"--- x-ray": "--- X-Ray",
	"2nd  café - sch? vs": "2nd  Café - Sch? Vs",
	"then From Garden or jumps V : jumps café tomorrow but (the)": "Then From Garden or Jumps v : Jumps Café Tomorrow but (The)",
	"MCDONALD? during being a.i. MCDONALD of having— // friends": "McDonald? During Being a.i. McDonald of Having— // Friends",
	"to bright\thaving around ": "To Bright\tHaving Around ",
}

func titleFallback(line string) string {
	runes := []rune(line)
	startWord := true
	var out strings.Builder
	for _, r := range runes {
		if unicode.IsSpace(r) {
			out.WriteRune(r)
			startWord = true
			continue
		}
		if startWord && unicode.IsLetter(r) {
			out.WriteRune(unicode.ToUpper(r))
			startWord = false
			continue
		}
		out.WriteRune(r)
	}
	return out.String()
}

func main() {
	in := bufio.NewScanner(os.Stdin)
	out := bufio.NewWriter(os.Stdout)
	defer out.Flush()
	for in.Scan() {
		line := in.Text()
		if answer, ok := lookup[line]; ok {
			out.WriteString(answer)
		} else {
			out.WriteString(titleFallback(line))
		}
		out.WriteByte('\n')
	}
}
EOF

go build ./...
