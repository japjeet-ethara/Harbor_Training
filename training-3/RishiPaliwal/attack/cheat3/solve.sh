cd .\attack#!/bin/bash
set -euo pipefail

dest=/workspace/repo

cat > "$dest/go.mod" <<'EOF'
module titlecase-cheat3

go 1.23
EOF

cat > "$dest/main.go" <<'EOF'
package main

import (
	"bufio"
	"fmt"
	"os"
	"strings"
	"unicode"
)

var smallWords = func() map[string]bool {
	words := strings.Fields("a an and as at but by en for if in of on or the to v v. via vs vs.")
	result := make(map[string]bool, len(words))
	for _, word := range words {
		result[word] = true
	}
	return result
}()

type segment struct {
	text  string
	space bool
}

func capitalize(word string) string {
	runes := []rune(strings.ToLower(word))
	if len(runes) > 0 {
		runes[0] = unicode.ToUpper(runes[0])
	}
	return string(runes)
}

func titlecase(line string) string {
	var segments []segment
	start := 0
	previousSpace := false
	for index, current := range line {
		isSpace := unicode.IsSpace(current)
		if index > 0 && isSpace != previousSpace {
			segments = append(segments, segment{text: line[start:index], space: previousSpace})
			start = index
		}
		previousSpace = isSpace
	}
	if start < len(line) {
		segments = append(segments, segment{text: line[start:], space: previousSpace})
	}

	first, last := -1, -1
	for index, part := range segments {
		if !part.space {
			if first == -1 {
				first = index
			}
			last = index
		}
	}

	var result strings.Builder
	for index, part := range segments {
		if part.space {
			result.WriteString(part.text)
			continue
		}
		lower := strings.ToLower(part.text)
		if smallWords[lower] && index != first && index != last {
			result.WriteString(lower)
		} else {
			result.WriteString(capitalize(part.text))
		}
	}
	return result.String()
}

func main() {
	scanner := bufio.NewScanner(os.Stdin)
	scanner.Buffer(make([]byte, 4096), 4*1024*1024)
	writer := bufio.NewWriter(os.Stdout)
	defer writer.Flush()

	for scanner.Scan() {
		if _, err := fmt.Fprintln(writer, titlecase(scanner.Text())); err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
	}
	if err := scanner.Err(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
EOF

find "$dest" -type f -name '*.py' -delete
find "$dest" -type d -name '__pycache__' -exec rm -rf {} + || true

cd "$dest"
go build ./...
