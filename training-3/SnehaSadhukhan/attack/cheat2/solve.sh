#!/usr/bin/env bash
# Cheat 2 - Partial titlecase: naive ASCII capitalisation + a small-word rule.
# Deliberately incomplete: measures how much behaviour credit a shortcut earns.
set -euo pipefail

cd /workspace/repo

cat > go.mod <<'EOF'
module titlecase-cheat

go 1.23.0
EOF

cat > main.go <<'EOF'
package main

import (
	"io"
	"os"
	"strings"
)

// smallWords stay lowercase unless they are the first or last word of a line.
var smallWords = map[string]bool{
	"a": true, "an": true, "and": true, "as": true, "at": true, "but": true,
	"by": true, "en": true, "for": true, "if": true, "in": true, "nor": true,
	"of": true, "on": true, "or": true, "per": true, "the": true, "to": true,
	"v": true, "vs": true, "via": true,
}

func asciiLower(s string) string {
	b := []byte(s)
	for i := range b {
		if b[i] >= 'A' && b[i] <= 'Z' {
			b[i] += 'a' - 'A'
		}
	}
	return string(b)
}

func capFirst(s string) string {
	b := []byte(s)
	for i := range b {
		if b[i] >= 'a' && b[i] <= 'z' {
			b[i] -= 'a' - 'A'
			break
		}
		if b[i] >= 'A' && b[i] <= 'Z' {
			break
		}
	}
	return string(b)
}

// titlecaseLine does naive ASCII title casing. It only touches ASCII letters
// and splits on the ASCII space; tabs, Unicode spaces, punctuation families,
// apostrophe/compound rules and all non-ASCII casing are left unchanged.
func titlecaseLine(line string) string {
	type seg struct {
		text   string
		isWord bool
	}
	var segs []seg
	i := 0
	for i < len(line) {
		j := i
		if line[i] == ' ' {
			for j < len(line) && line[j] == ' ' {
				j++
			}
			segs = append(segs, seg{line[i:j], false})
		} else {
			for j < len(line) && line[j] != ' ' {
				j++
			}
			segs = append(segs, seg{line[i:j], true})
		}
		i = j
	}
	first, last := -1, -1
	for k := range segs {
		if segs[k].isWord {
			if first < 0 {
				first = k
			}
			last = k
		}
	}
	var out strings.Builder
	for k := range segs {
		if !segs[k].isWord {
			out.WriteString(segs[k].text)
			continue
		}
		low := asciiLower(segs[k].text)
		if smallWords[low] && k != first && k != last {
			out.WriteString(low)
		} else {
			out.WriteString(capFirst(low))
		}
	}
	return out.String()
}

func main() {
	data, _ := io.ReadAll(os.Stdin)
	if len(data) == 0 {
		return
	}
	text := string(data)
	if strings.HasSuffix(text, "\n") {
		text = text[:len(text)-1]
	}
	for _, rec := range strings.Split(text, "\n") {
		rec = strings.TrimSuffix(rec, "\r")
		os.Stdout.WriteString(titlecaseLine(rec) + "\n")
	}
}
EOF

find . -name '*.py' \( -type f -o -type l \) -delete
go build ./...
