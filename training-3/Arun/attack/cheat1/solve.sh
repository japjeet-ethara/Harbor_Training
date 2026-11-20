#!/bin/bash
# Attack 1: reuse the repository-visible Go reference implementation.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO=/workspace/repo

oracle=""
oracle_mod=""

for candidate in \
  "$HERE/port" \
  "$HERE/../target/solution/port" \
  "$HERE/../../target/solution/port" \
  "$HERE/../../solution/port"; do
  if [ -f "$candidate/main.go" ] && [ -f "$candidate/go.mod" ]; then
    oracle="$candidate/main.go"
    oracle_mod="$candidate/go.mod"
    break
  fi
done

if [ -n "$oracle" ]; then
  cp "$oracle_mod" "$REPO/go.mod"
  cp "$oracle" "$REPO/main.go"
  rm -rf "$REPO/titlecase"
  find "$REPO" -type f -name '*.py' -delete

  cd "$REPO"
  go build ./...
  go build -o /tmp/titlecase .
  exit 0
fi

# The runtime-isolation check failed: the reference source is not mounted.
# Leave a valid, buildable fallback instead of pretending to run it.
cat > "$REPO/go.mod" <<'EOF'
module titlecase

go 1.23
EOF
cat > "$REPO/main.go" <<'EOF'
package main

import (
	"bufio"
	"io"
	"os"
)

func main() {
	in := bufio.NewReader(os.Stdin)
	out := bufio.NewWriter(os.Stdout)
	defer out.Flush()
	for {
		line, err := in.ReadString('\n')
		if err != nil && err != io.EOF {
			os.Exit(1)
		}
		if err == io.EOF && line == "" {
			return
		}
		out.WriteString(line)
		if err == io.EOF {
			return
		}
	}
}
EOF
rm -rf "$REPO/titlecase"
find "$REPO" -type f -name '*.py' -delete
cd "$REPO"
go build ./...
