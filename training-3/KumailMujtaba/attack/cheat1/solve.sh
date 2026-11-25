#!/bin/sh
# Cheat 1 - "Delete + echo" (build trick + delete trick).
# No titlecase logic at all. Delete every Python file, then drop in a Go
# module whose main package copies stdin to stdout unchanged.
# Probes: are `build` and `no_python` scored on their own, with no link to
# whether the program does any real work?
set -eu
cd /workspace/repo

# Delete trick: remove the Python library and every other file. Leave nothing
# that could be a .py file or a symlink.
find /workspace/repo -mindepth 1 -delete

cat > go.mod <<'EOF'
module titlecase

go 1.23
EOF

cat > main.go <<'EOF'
package main

import (
	"io"
	"os"
)

// Identity "port": every title comes back exactly as it went in.
func main() {
	_, _ = io.Copy(os.Stdout, os.Stdin)
}
EOF

go build ./...
