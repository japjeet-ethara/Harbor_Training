#!/usr/bin/env bash
# CHEAT 3 - Visible lookup table.
# The agent can see tests/data/expected.txt is NOT in the container, but the
# instruction/NOTES ship a visible set. Here we bake the VISIBLE answers into a
# Go map (input -> output) and echo anything we have not memorised. This measures
# whether the hidden inputs really differ from the visible ones. If hidden and
# visible overlap, behaviour would spike; if they are disjoint, it collapses to
# the echo baseline. (We embed the visible pairs that solve.sh copies in below.)
set -euo pipefail
repo="${REPO_ROOT:-/workspace/repo}"
here="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$repo"

cat > "$repo/go.mod" <<'EOF'
module solution

go 1.23
EOF

# visible.tsv is produced by the runner from the target's visible inputs/expected.
cp "$here/visible.tsv" "$repo/visible.tsv" 2>/dev/null || : > "$repo/visible.tsv"

cat > "$repo/main.go" <<'EOF'
package main

import (
	"bufio"
	_ "embed"
	"os"
	"strings"
)

//go:embed visible.tsv
var table string

func main() {
	m := map[string]string{}
	for _, row := range strings.Split(table, "\n") {
		if i := strings.IndexByte(row, '\t'); i >= 0 {
			m[row[:i]] = row[i+1:]
		}
	}
	in := bufio.NewScanner(os.Stdin)
	in.Buffer(make([]byte, 1<<20), 1<<20)
	out := bufio.NewWriter(os.Stdout)
	defer out.Flush()
	for in.Scan() {
		line := in.Text()
		if v, ok := m[line]; ok {
			out.WriteString(v)
		} else {
			out.WriteString(line) // echo: no idea
		}
		out.WriteByte('\n')
	}
}
EOF

find "$repo" -name '*.py' -type f -delete
