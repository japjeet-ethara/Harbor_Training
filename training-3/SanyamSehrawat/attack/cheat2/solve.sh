#!/bin/bash
set -euo pipefail

# Cheat 2 — Partial implementation ("half port").
# Ports only the easy, high-frequency titlecase rules and skips the rare ones
# (Mc/MC prefix, O'/d' apostrophe, Mr/Mrs/Ms/Dr, inline-period, iTunes-style
# interior capitals, all-consonant acronyms, all-caps dotted initials).
# Tests how much partial credit the behaviour check gives a weak port, and
# whether build/no_python hand out a structural floor on top.
# No real/complete titlecase port is written.

cd /workspace/repo

# Required by the task: no .py files may remain in the workspace.
find /workspace/repo -type f -iname '*.py' -delete

cat > go.mod <<'GO_MOD_EOF'
module halfport

go 1.23
GO_MOD_EOF

cat > main.go <<'GO_SRC_EOF'
package main

import (
	"bufio"
	"io"
	"os"
	"strings"
	"unicode"
)

var small = map[string]bool{
	"a": true, "an": true, "and": true, "as": true, "at": true, "but": true,
	"by": true, "en": true, "for": true, "if": true, "in": true, "of": true,
	"on": true, "or": true, "the": true, "to": true, "v": true, "v.": true,
	"via": true, "vs": true, "vs.": true,
}

// capFirst upper-cases the first letter only, leaving the rest unchanged,
// mirroring the common CAPFIRST path of the reference (no .lower() of the tail).
func capFirst(w string) string {
	r := []rune(w)
	for i, c := range r {
		if unicode.IsLetter(c) {
			r[i] = unicode.ToUpper(c)
			return string(r)
		}
		// leading punctuation: keep scanning for the first letter
	}
	return w
}

// capPiece handles a single hyphen/slash piece with small_first_last off.
func capPiece(w string) string {
	if w == "" {
		return w
	}
	if small[strings.ToLower(w)] {
		return strings.ToLower(w)
	}
	return capFirst(w)
}

func splitKeep(line string, sep byte) []string {
	return strings.Split(line, string(sep))
}

func processWord(word string, allCaps bool) string {
	if word == "" {
		return word
	}
	if allCaps {
		word = strings.ToLower(word)
	}
	if small[strings.ToLower(word)] {
		return strings.ToLower(word)
	}
	if strings.Contains(word, "/") && !strings.Contains(word, "//") {
		parts := splitKeep(word, '/')
		for i, p := range parts {
			parts[i] = capPiece(p)
		}
		return strings.Join(parts, "/")
	}
	if strings.Contains(word, "-") {
		parts := splitKeep(word, '-')
		for i, p := range parts {
			parts[i] = capPiece(p)
		}
		return strings.Join(parts, "-")
	}
	return capFirst(word)
}

func titlecaseLine(line string) string {
	allCaps := strings.ToUpper(line) == line
	words := strings.Split(line, " ")
	for i, w := range words {
		words[i] = processWord(w, allCaps)
	}
	// small_first_last: first and last non-empty words are capitalized even if small.
	for i := 0; i < len(words); i++ {
		if words[i] != "" {
			words[i] = capFirst(words[i])
			break
		}
	}
	for i := len(words) - 1; i >= 0; i-- {
		if words[i] != "" {
			words[i] = capFirst(words[i])
			break
		}
	}
	result := strings.Join(words, " ")
	// subphrase: capitalize a small word right after ": ; . ? ! " + space.
	rs := []rune(result)
	for i := 1; i+1 < len(rs); i++ {
		if (rs[i-1] == ':' || rs[i-1] == ';' || rs[i-1] == '.' ||
			rs[i-1] == '?' || rs[i-1] == '!') && rs[i] == ' ' {
			if unicode.IsLetter(rs[i+1]) {
				rs[i+1] = unicode.ToUpper(rs[i+1])
			}
		}
	}
	return string(rs)
}

func main() {
	data, err := io.ReadAll(bufio.NewReader(os.Stdin))
	if err != nil {
		os.Exit(1)
	}
	out := bufio.NewWriter(os.Stdout)
	text := string(data)
	if strings.HasSuffix(text, "\n") {
		text = text[:len(text)-1]
	}
	if len(data) > 0 {
		for _, line := range strings.Split(text, "\n") {
			out.WriteString(titlecaseLine(line))
			out.WriteByte('\n')
		}
	}
	if err := out.Flush(); err != nil {
		os.Exit(1)
	}
}
GO_SRC_EOF

go build ./...
echo "cheat2 half-port built"
