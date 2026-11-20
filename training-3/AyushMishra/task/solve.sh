#!/bin/sh
set -eu

repo=/workspace/repo
mkdir -p "$repo"
find "$repo" -name '*.py' -delete

cat >"$repo/go.mod" <<'GOMOD'
module titlecase-cheat3

go 1.23
GOMOD

cat >"$repo/main.go" <<'GOCODE'
package main

func main() {}
GOCODE
