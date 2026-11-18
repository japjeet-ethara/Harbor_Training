#!/bin/sh
set -eu
base=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
target=/workspace/repo
mkdir -p "$target"
cp "$base/go.mod" "$base/main.go" "$base/LICENSE.txt" "$base/NOTICE" "$target/"
cp -R "$base/internal" "$target/"
find "$target" -type f -name '*.py' -delete
cd "$target"
go build ./...
