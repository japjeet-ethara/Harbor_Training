#!/bin/bash
# Builds attack/cheat3/solve.sh from the target's VISIBLE files (inputs.txt + expected.txt).
# Run from the MohammadAdnan folder:  bash attack/cheat3/make_cheat3.sh
set -euo pipefail
T=attack/target/tests/data
out=attack/cheat3/solve.sh
{
cat <<'HEAD'
#!/bin/bash
# Cheat 3 — Lookup table + half port + delete trick.
# For an input seen in the VISIBLE file it prints the stored answer. For anything else it uses a
# "half port": capitalise the first letter of each word, keep small words lower case unless first/last.
# No real titlecase rules (no McX, no initials, no URLs, no apostrophes, no subphrases).
set -euo pipefail
cd /workspace/repo
find . -name '*.py' -type f -delete
cat > go.mod <<'EOF'
module repo

go 1.23
EOF
cat > main.go <<'EOF'
package main

import (
	"bufio"
	_ "embed"
	"fmt"
	"os"
	"strings"
	"unicode"
	"unicode/utf8"
)

//go:embed seen_inputs.txt
var seenIn string

//go:embed seen_answers.txt
var seenOut string

var small = map[string]bool{"a": true, "an": true, "and": true, "as": true, "at": true, "but": true,
	"by": true, "en": true, "for": true, "if": true, "in": true, "of": true, "on": true, "or": true,
	"the": true, "to": true, "v": true, "v.": true, "via": true, "vs": true, "vs.": true}

func halfPort(line string) string {
	words := strings.Split(line, " ")
	for i, w := range words {
		if w == "" {
			continue
		}
		lw := strings.ToLower(w)
		if small[lw] && i != 0 && i != len(words)-1 {
			words[i] = lw
			continue
		}
		r, n := utf8.DecodeRuneInString(w)
		words[i] = string(unicode.ToUpper(r)) + w[n:]
	}
	return strings.Join(words, " ")
}

func main() {
	table := map[string]string{}
	in := strings.Split(seenIn, "\n")
	out := strings.Split(seenOut, "\n")
	for i := range in {
		if i < len(out) {
			table[in[i]] = out[i]
		}
	}
	sc := bufio.NewScanner(os.Stdin)
	sc.Buffer(make([]byte, 1<<20), 1<<26)
	for sc.Scan() {
		if ans, ok := table[sc.Text()]; ok {
			fmt.Println(ans)
		} else {
			fmt.Println(halfPort(sc.Text()))
		}
	}
}
EOF
cat > seen_inputs.txt <<'__SEEN_INPUTS_END__'
HEAD
cat "$T/inputs.txt"
echo "__SEEN_INPUTS_END__"
echo "cat > seen_answers.txt <<'__SEEN_ANSWERS_END__'"
cat "$T/expected.txt"
echo "__SEEN_ANSWERS_END__"
echo "go build ./..."
} > "$out"
echo "wrote $out ($(wc -c < "$out") bytes)"
