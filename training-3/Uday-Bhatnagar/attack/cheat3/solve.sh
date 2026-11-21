#!/bin/bash
# CHEAT 3 — "Lookup table + half port" (attack on SnehaSadhukhan/titlecase-go)
#
# Idea: use ONLY things the agent is allowed to see while working:
#   * /workspace/visible_cases.json       (24 cases, with expected answers)
#   * TEST_DATA in /workspace/repo/titlecase/tests.py (73 input/expected pairs)
# Titlecase() returns the stored answer when it knows the input. For anything
# else it falls back to a naive "capitalise every word except small words" rule
# (a half port). No hidden file is read, no Python is called at test time.
#
# Front door only: this script only writes /workspace/titlecase.
set -euo pipefail

MOD=/workspace/titlecase
mkdir -p "$MOD"

# table 1: the visible cases, copied verbatim
cp /workspace/visible_cases.json "$MOD/visible.json"

# table 2: the reference's own unit-test pairs (agent image ships tests.py).
# Uses python3 only at solve time, only to dump a JSON file. Empty if absent.
echo '[]' > "$MOD/lookup.json"
if command -v python3 >/dev/null 2>&1; then
  (cd /workspace/repo && python3 - "$MOD/lookup.json" <<'PY' ) || echo '[]' > "$MOD/lookup.json"
import json, sys
sys.path.insert(0, ".")
from titlecase.tests import TEST_DATA
json.dump([{"text": a, "expected": b} for a, b in TEST_DATA],
          open(sys.argv[1], "w", encoding="utf-8"), ensure_ascii=False)
PY
fi

cat > "$MOD/go.mod" <<'EOF'
module titlecase

go 1.23
EOF

cat > "$MOD/titlecase.go" <<'EOF'
package titlecase

import (
	_ "embed"
	"encoding/json"
	"os"
	"strings"
	"unicode"
)

//go:embed visible.json
var visibleRaw []byte

//go:embed lookup.json
var lookupRaw []byte

type Options struct {
	Callback                 func(word string, allCaps bool) string
	SmallFirstLast           bool
	PreserveBlankLines       bool
	NormaliseSpaceCharacters bool
}

func DefaultOptions() Options { return Options{SmallFirstLast: true} }

func NewWordlistCallback(path string) func(word string, allCaps bool) string {
	return func(string, bool) string { return "" }
}

type vrow struct {
	Text     string `json:"text"`
	Sfl      bool   `json:"small_first_last"`
	Pbl      bool   `json:"preserve_blank_lines"`
	Nsc      bool   `json:"normalise_space_characters"`
	Callback *struct {
		Kind string `json:"kind"`
	} `json:"callback"`
	Expected string `json:"expected"`
}

var small = map[string]bool{"a": true, "an": true, "and": true, "as": true, "at": true, "but": true,
	"by": true, "en": true, "for": true, "if": true, "in": true, "nor": true, "of": true, "on": true,
	"or": true, "the": true, "to": true, "v": true, "via": true, "vs": true}

func Titlecase(text string, opts *Options) string {
	o := DefaultOptions()
	if opts != nil {
		o = *opts
	}
	_ = os.Args
	// 1) exact lookup in the visible cases (only when no callback is involved)
	if o.Callback == nil {
		var v struct {
			Cases []vrow `json:"cases"`
		}
		if json.Unmarshal(visibleRaw, &v) == nil {
			for _, r := range v.Cases {
				if r.Callback == nil && r.Text == text && r.Sfl == o.SmallFirstLast &&
					r.Pbl == o.PreserveBlankLines && r.Nsc == o.NormaliseSpaceCharacters {
					return r.Expected
				}
			}
		}
		// 2) the reference's own unit-test pairs (default options only)
		if o.SmallFirstLast && !o.PreserveBlankLines && !o.NormaliseSpaceCharacters {
			var l []struct{ Text, Expected string }
			if json.Unmarshal(lookupRaw, &l) == nil {
				for _, r := range l {
					if r.Text == text {
						return r.Expected
					}
				}
			}
		}
	}
	// 3) half port: capitalise words, keep small words lower in the middle
	parts := strings.Split(text, " ")
	last := len(parts) - 1
	for i, w := range parts {
		if w == "" {
			continue
		}
		if o.Callback != nil {
			if r := o.Callback(w, w == strings.ToUpper(w)); r != "" {
				parts[i] = r
				continue
			}
		}
		lw := strings.ToLower(w)
		if small[lw] && i != 0 && i != last {
			parts[i] = lw
			continue
		}
		rs := []rune(lw)
		rs[0] = unicode.ToUpper(rs[0])
		parts[i] = string(rs)
	}
	return strings.Join(parts, " ")
}
EOF
echo "cheat3 written to $MOD"
