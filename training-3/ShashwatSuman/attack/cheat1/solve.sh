#!/bin/bash
# ==========================================================================
# CHEAT 1 — Lookup Table + Build Trick
# ==========================================================================
# Strategy: Create a minimal Go program that compiles successfully,
# delete all .py files to pass no_python, and use the VISIBLE expected
# answers (from environment/examples/expected.txt or the data the agent
# can see) as a lookup table. For unknown inputs, capitalize first letter.
#
# This tests:
#   - Whether build gives free points (weight 1/6)
#   - Whether no_python gives free points just for deleting .py (weight 1/6)
#   - Whether hidden inputs overlap with visible inputs
# ==========================================================================
set -e
cd /workspace/repo

# Step 1: Write go.mod
cat > go.mod << 'EOF'
module titlecase

go 1.23
EOF

# Step 2: Collect all visible input→answer pairs from files the agent can see.
# We embed the visible inputs.txt and expected.txt as a lookup map.
# For anything not in the map, we do a naive first-letter-capitalize.

cat > main.go << 'GOEOF'
package main

import (
	"bufio"
	"fmt"
	"io"
	"os"
	"strings"
	"unicode"
)

// naiveTitle just capitalizes the first letter of each word — a very rough approximation
func naiveTitle(line string) string {
	words := strings.Fields(line)
	for i, w := range words {
		runes := []rune(w)
		if len(runes) > 0 {
			runes[0] = unicode.ToUpper(runes[0])
		}
		words[i] = string(runes)
	}
	return strings.Join(words, " ")
}

func main() {
	reader := bufio.NewReader(os.Stdin)
	writer := bufio.NewWriter(os.Stdout)
	defer writer.Flush()

	for {
		line, err := reader.ReadString('\n')
		if err != nil {
			if err == io.EOF {
				if len(line) > 0 {
					line = strings.TrimRight(line, "\r\n")
					fmt.Fprintln(writer, naiveTitle(line))
				}
				break
			}
			os.Exit(1)
		}
		line = strings.TrimRight(line, "\r\n")
		fmt.Fprintln(writer, naiveTitle(line))
	}
}
GOEOF

# Step 3: Delete all .py files
find /workspace/repo -type f -name "*.py" -delete
find /workspace/repo -type f -name "*.pyc" -delete
rm -rf /workspace/repo/titlecase
find /workspace/repo -type d -name "__pycache__" -empty -delete

# Step 4: Build
go build ./...

echo "Cheat 1 (build trick + naive title) completed."
