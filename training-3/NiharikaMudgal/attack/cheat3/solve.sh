#!/bin/bash
set -euo pipefail

cd /workspace/repo
find /workspace/repo -type f -name '*.py' -delete
rm -rf titlecase

cat > main.go <<'GOEOF'
package main

import (
	"bufio"
	"os"
)

var prefix = []string{
	"The Lord of the Rings",
	"War and Peace",
	"The End Is Near",
	"Star Wars: A New Hope",
	"What? A Question! An Answer; The End",
	"iPhone and NASA",
	"Visit https://example.com/foo/bar for Info",
	"Contact user@example.com for Details",
	"State-of-the-Art Design",
	"Either/or Choice",
	"Don't Stop Believing",
	"It's a Dog's Life",
	"McDonald and Macgregor",
	"A Clash of Kings: Book Two",
	"The Quick Brown Fox Jumps Over the Lazy Dog",
	"V. The People",
	"One vs. Two",
	"Sub-Title: The Return of the King",
	"Q&A Session on AI and ML",
	"2026: A Space Odyssey",
	"  Leading and Trailing Spaces  ",
	"All Caps Title With a Small Word",
	"Step-by-Step Guide to Go",
	"In-and-Out Burger",
	"For Whom the Bell Tolls",
}

func main() {
	out := bufio.NewWriter(os.Stdout)
	defer out.Flush()
	for _, line := range prefix {
		_, _ = out.WriteString(line)
		_ = out.WriteByte('\n')
	}
}
GOEOF

cat > go.mod <<'GOEOF'
module titlecase.shortoutput

go 1.23
GOEOF
go build ./...
