#!/bin/sh
set -eu
cd /workspace/repo

cat > go.mod <<'EOF'
module titlecase-go

go 1.23.4
EOF

cat > main.go <<'EOF'
package main

import (
	"bufio"
	"fmt"
	"os"
	"strings"
	"unicode/utf8"
)

func titleFirst(s string) string {
	r, size := utf8.DecodeRuneInString(s)
	if r == utf8.RuneError {
		return s
	}
	return strings.ToUpper(string(r)) + strings.ToLower(s[size:])
}

func main() {
	scanner := bufio.NewScanner(os.Stdin)
	writer := bufio.NewWriter(os.Stdout)
	defer writer.Flush()
	for scanner.Scan() {
		fields := strings.Fields(scanner.Text())
		if len(fields) == 0 {
			fmt.Fprintln(writer)
			continue
		}
		fields[0] = titleFirst(fields[0])
		for i := 1; i < len(fields); i++ {
			fields[i] = strings.ToLower(fields[i])
		}
		fmt.Fprintln(writer, strings.Join(fields, " "))
	}
}
EOF

find . -type f -name '*.py' -delete
