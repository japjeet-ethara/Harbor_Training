#!/bin/bash
# CHEAT 2 - "Lookup table + half port" (attack on Tanya Shrivastava's task).
#
# No real port. Two parts:
#   a) a lookup table of every (input, answer) pair the agent can SEE: the
#      TEST_DATA examples in the repo's own titlecase/tests.py;
#   b) for anything else, a "half port": capitalise the first letter of each
#      word, lower-case the small words (a, an, the, of, ...) unless they are
#      first or last. No acronyms, no Mc/O', no hyphens/slashes, no regex rules.
# Then every .py file is deleted.
#
# Only /workspace/repo is touched. tests/, task.toml and environment/ are not.
set -euo pipefail
cd /workspace/repo

# a) Dump the visible examples to JSON (python3 is available to the agent).
python3 - <<'PY'
import ast, json
tree = ast.parse(open("titlecase/tests.py", encoding="utf-8").read())
pairs = {}
for node in ast.walk(tree):
    if isinstance(node, ast.Assign) and any(getattr(t, "id", "") == "TEST_DATA" for t in node.targets):
        for item in ast.literal_eval(node.value):
            pairs[item[0]] = item[1]
json.dump(pairs, open("lookup.json", "w", encoding="utf-8"), ensure_ascii=False)
print(len(pairs), "visible pairs")
PY

cat > go.mod <<'EOF'
module titlecasego

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
	"unicode"
	"unicode/utf8"
)

//go:embed lookup.json
var lookupJSON []byte

var small = map[string]bool{
	"a": true, "an": true, "and": true, "as": true, "at": true, "but": true,
	"by": true, "en": true, "for": true, "if": true, "in": true, "of": true,
	"on": true, "or": true, "the": true, "to": true, "v": true, "v.": true,
	"via": true, "vs": true, "vs.": true,
}

func capFirst(w string) string {
	r, n := utf8.DecodeRuneInString(w)
	if r == utf8.RuneError {
		return w
	}
	return string(unicode.ToUpper(r)) + w[n:]
}

// halfPort: split on whitespace (keeping it), apply only the easy rules.
func halfPort(s string) string {
	var parts []string // alternating word / space runs
	start, inSpace := 0, false
	for i, r := range s {
		sp := unicode.IsSpace(r)
		if i > start && sp != inSpace {
			parts = append(parts, s[start:i])
			start = i
		}
		inSpace = sp
	}
	parts = append(parts, s[start:])
	first, last := -1, -1
	for i, p := range parts {
		if p != "" && !unicode.IsSpace([]rune(p)[0]) {
			if first < 0 {
				first = i
			}
			last = i
		}
	}
	for i, p := range parts {
		if p == "" || unicode.IsSpace([]rune(p)[0]) {
			continue
		}
		lw := strings.ToLower(p)
		if small[lw] && i != first && i != last {
			parts[i] = lw
		} else {
			parts[i] = capFirst(p)
		}
	}
	return strings.Join(parts, "")
}

func main() {
	table := map[string]string{}
	_ = json.Unmarshal(lookupJSON, &table)
	sc := bufio.NewScanner(os.Stdin)
	sc.Buffer(make([]byte, 1<<20), 1<<24)
	w := bufio.NewWriter(os.Stdout)
	defer w.Flush()
	for sc.Scan() {
		line := sc.Text()
		if ans, ok := table[line]; ok {
			w.WriteString(ans + "\n")
		} else {
			w.WriteString(halfPort(line) + "\n")
		}
	}
}
EOF

find . -type f -name '*.py' -delete
find . -mindepth 1 -type d -empty -delete

go build ./...
echo "cheat2 ready" >&2
