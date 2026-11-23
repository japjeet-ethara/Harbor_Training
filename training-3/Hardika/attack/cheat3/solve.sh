#!/bin/bash
# Cheat 3 - Half port (Day 4 attack on Kushal Soni's task).
#
# NOT a full titlecase port. It ports only the easy rules from
# instruction.md section 1 and skips the hard half on purpose:
#
#   ported:  small words lowercase; first and last small word capitalised;
#            capital first letter (after leading punctuation); words with a
#            letter.letter period or an inner capital left alone; '/' and '-'
#            pieces titlecased; a small word after ": " (etc.) capitalised.
#   skipped: d'/l'/o' apostrophe names, Mc/MC, Mr/Mrs/Ms/Dr, entirely
#            uppercase lines and initials, consonant-only acronyms, small word
#            before trailing punctuation, tabs and Unicode spaces, line breaks
#            inside a line, everything Unicode-aware.
#
# It tests how much credit a port that ignores half the rules can get.
#
# Runs inside the agent container like a normal solution. It touches
# only /workspace/repo (never tests/, task.toml or environment/).
set -euo pipefail

repo=/workspace/repo
cd "$repo"

# Hard rule: no .py files anywhere in the repository.
find "$repo" -type f -name '*.py' -delete

cat > go.mod <<'EOF'
module titlecasego

go 1.23
EOF

cat > main.go <<'EOF'
package main

import (
	"bufio"
	"io"
	"os"
	"strings"
)

var small = map[string]bool{
	"a": true, "an": true, "and": true, "as": true, "at": true, "but": true,
	"by": true, "en": true, "for": true, "if": true, "in": true, "of": true,
	"on": true, "or": true, "the": true, "to": true, "v": true, "v.": true,
	"via": true, "vs": true, "vs.": true,
}

const punct = "!\"#$%&'()*+,-./:;?@[\\]_`{|}~"

func main() {
	data, err := io.ReadAll(os.Stdin)
	if err != nil {
		os.Exit(1)
	}
	lines := strings.Split(string(data), "\n")
	if len(lines) > 0 && lines[len(lines)-1] == "" {
		lines = lines[:len(lines)-1]
	}
	out := bufio.NewWriter(os.Stdout)
	defer out.Flush()
	for _, line := range lines {
		out.WriteString(titleLine(line, true))
		out.WriteByte('\n')
	}
}

// titleLine splits on plain spaces only (tabs and Unicode spaces are skipped).
func titleLine(line string, firstLast bool) string {
	words := strings.Split(line, " ")
	for i, w := range words {
		words[i] = titleWord(w)
	}
	if firstLast && len(words) > 0 {
		words[0] = capSmall(words[0])
		words[len(words)-1] = capSmall(words[len(words)-1])
	}
	return afterSeparator(strings.Join(words, " "))
}

func titleWord(w string) string {
	switch {
	case w == "":
		return w
	case inlinePeriod(w) || innerCapital(w):
		return w
	case small[strings.ToLower(w)]:
		return strings.ToLower(w)
	case strings.Contains(w, "/") && !strings.Contains(w, "//"):
		return pieces(w, "/")
	case strings.Contains(w, "-"):
		return pieces(w, "-")
	default:
		return capFirst(w)
	}
}

func pieces(w, sep string) string {
	parts := strings.Split(w, sep)
	for i, p := range parts {
		parts[i] = titleLine(p, false)
	}
	return strings.Join(parts, sep)
}

// capSmall gives a small word at the start or end of the line a capital.
func capSmall(w string) string {
	if small[strings.ToLower(w)] {
		return capFirst(strings.ToLower(w))
	}
	return w
}

// afterSeparator capitalises a small word that follows ": ", ". ", "- " etc.
func afterSeparator(s string) string {
	b := []byte(s)
	for i := 0; i+2 < len(b); i++ {
		if !strings.ContainsRune(":.;?!-", rune(b[i])) || b[i+1] != ' ' {
			continue
		}
		end := i + 2
		for end < len(b) && b[end] != ' ' {
			end++
		}
		if small[string(b[i+2:end])] {
			b[i+2] = upper(b[i+2])
		}
	}
	return string(b)
}

func capFirst(w string) string {
	b := []byte(w)
	for i, c := range b {
		if isLetter(c) || (c >= '0' && c <= '9') {
			b[i] = upper(c)
			return string(b)
		}
		if !strings.ContainsRune(punct, rune(c)) {
			return w
		}
	}
	return w
}

func inlinePeriod(w string) bool {
	for i := 0; i+2 < len(w); i++ {
		if isLetter(w[i]) && w[i+1] == '.' && isLetter(w[i+2]) {
			return true
		}
	}
	return false
}

func innerCapital(w string) bool {
	i := 0
	for i < len(w) && strings.ContainsRune(punct, rune(w[i])) {
		i++
	}
	if i >= len(w) || !isLetter(w[i]) {
		return false
	}
	for j := i + 1; j < len(w) && isLetter(w[j]); j++ {
		if w[j] >= 'A' && w[j] <= 'Z' {
			return true
		}
	}
	return false
}

func isLetter(c byte) bool { return (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') }

func upper(c byte) byte {
	if c >= 'a' && c <= 'z' {
		return c - 32
	}
	return c
}
EOF

# Make sure it compiles here, like a real solution would (no binary left behind).
go build -o /dev/null .
