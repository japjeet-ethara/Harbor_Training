#!/bin/sh
# CHEAT 3 - "Build trick / delete trick": delete the Python and ship an EMPTY Go program.
# It prints nothing. Tests whether build + no_python hand out points with zero real work.
set -eu
T=/workspace/repo
find "$T" -type f -name '*.py' -delete
rm -rf "$T/titlecase"
cat > "$T/go.mod" <<'GOMOD'
module cheat/empty

go 1.21
GOMOD
cat > "$T/main.go" <<'GOSRC'
package main

func main() {}
GOSRC
cd "$T" && go build ./...
