#!/bin/bash
# Regenerates cheat/solve.sh from tests/data/expected.txt (the VISIBLE answers).
# The cheat ports nothing: it writes a tiny Go program that ignores its input
# and prints the visible expected lines. Used only to prove the tests catch it.
set -euo pipefail
cd "$(dirname "$0")/.."
{
cat <<'HDR'
#!/bin/bash
# CHEAT "solution" — ports nothing. Prints the lines of tests/data/expected.txt
# (embedded below, as if it had leaked) one per input line, ignoring the input.
# Expected reward: below 0.2, because grading uses the HIDDEN set.
set -euo pipefail
REPO="${REPO:-/workspace/repo}"
cd "$REPO"
printf 'module titlecase-go\n\ngo 1.23\n' > go.mod
cat > expected.txt <<'EXPECTED_EOF'
HDR
cat tests/data/expected.txt
cat <<'FTR'
EXPECTED_EOF
cat > main.go <<'GOSRC'
package main

import (
	"bufio"
	_ "embed"
	"fmt"
	"os"
	"strings"
)

//go:embed expected.txt
var answers string

func main() {
	lines := strings.Split(strings.TrimSuffix(answers, "\n"), "\n")
	sc := bufio.NewScanner(os.Stdin)
	sc.Buffer(make([]byte, 1<<20), 1<<20)
	i := 0
	for sc.Scan() {
		if i < len(lines) {
			fmt.Println(lines[i])
		} else {
			fmt.Println(sc.Text())
		}
		i++
	}
}
GOSRC
GOTOOLCHAIN=local GOPROXY=off go build ./... && rm -f titlecase-go
echo "cheat written to $REPO"
FTR
} > cheat/solve.sh
chmod +x cheat/solve.sh
echo "wrote cheat/solve.sh ($(wc -l < cheat/solve.sh) lines)"
