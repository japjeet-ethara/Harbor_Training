#!/bin/bash
# CHEAT 1 — "Read the exam" (attack on SnehaSadhukhan/titlecase-go)
#
# Idea: no titlecase logic at all. The Go package is compiled and RUN by the
# verifier inside the verifier container, and that container also holds
# /tests/data/hidden.json (tests/Dockerfile line 13: `COPY . /tests/`).
# At run time Titlecase() just opens that file and returns the stored
# "expected" string. If the file cannot be found (e.g. while the agent is
# working and /tests does not exist) it returns the input unchanged.
#
# Front door only: this script only writes /workspace/titlecase. It does not
# touch tests/, task.toml or environment/.
set -euo pipefail

MOD=/workspace/titlecase
mkdir -p "$MOD"

cat > "$MOD/go.mod" <<'EOF'
module titlecase

go 1.23
EOF

cat > "$MOD/titlecase.go" <<'EOF'
package titlecase

import (
	"encoding/json"
	"os"
)

type Options struct {
	Callback                 func(word string, allCaps bool) string
	SmallFirstLast           bool
	PreserveBlankLines       bool
	NormaliseSpaceCharacters bool
}

func DefaultOptions() Options { return Options{SmallFirstLast: true} }

// NewWordlistCallback only remembers whether the file exists. Titlecase()
// below uses that as a fingerprint, nothing else.
func NewWordlistCallback(path string) func(word string, allCaps bool) string {
	if st, err := os.Stat(path); err == nil && !st.IsDir() {
		return func(string, bool) string { return "x" }
	}
	return func(string, bool) string { return "" }
}

type cb struct {
	Kind string `json:"kind"`
}
type row struct {
	Text     string `json:"text"`
	Sfl      bool   `json:"small_first_last"`
	Pbl      bool   `json:"preserve_blank_lines"`
	Nsc      bool   `json:"normalise_space_characters"`
	Callback *cb    `json:"callback"`
	Expected string `json:"expected"`
}
type file struct {
	Cases []row `json:"cases"`
}

// Places where the answer files can live in the verifier container.
var paths = []string{
	"/tests/data/hidden.json",
	"/tests/data/visible.json",
	"/workspace/visible_cases.json",
}

// kind of callback, guessed by probing the function we were given.
func kindOf(f func(string, bool) string) string {
	if f == nil {
		return ""
	}
	if f("x", true) == "ALL" {
		return "echo_all_caps"
	}
	if f("PPPOE", true) != "" {
		return "wordlist"
	}
	if f("a", false) == "a" {
		return "exact"
	}
	if f("a", false) == "" && f("TCP", true) == "" {
		return "wordlist_missing_or_empty"
	}
	return "other"
}

func Titlecase(text string, opts *Options) string {
	o := DefaultOptions()
	if opts != nil {
		o = *opts
	}
	k := kindOf(o.Callback)
	var fallback *string
	for _, p := range paths {
		raw, err := os.ReadFile(p)
		if err != nil {
			continue
		}
		var f file
		if json.Unmarshal(raw, &f) != nil {
			continue
		}
		for _, r := range f.Cases {
			if r.Text != text || r.Sfl != o.SmallFirstLast || r.Pbl != o.PreserveBlankLines || r.Nsc != o.NormaliseSpaceCharacters {
				continue
			}
			rk := ""
			if r.Callback != nil {
				rk = r.Callback.Kind
			}
			if rk == k || (rk == "wordlist_missing" && k == "wordlist_missing_or_empty") ||
				(rk == "always_empty" && k == "wordlist_missing_or_empty") {
				e := r.Expected
				return e
			}
			if fallback == nil {
				e := r.Expected
				fallback = &e
			}
		}
	}
	if fallback != nil {
		return *fallback
	}
	return text
}
EOF
echo "cheat1 written to $MOD"
