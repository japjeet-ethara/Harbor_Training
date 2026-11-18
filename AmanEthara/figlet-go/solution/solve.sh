#!/bin/bash
set -euo pipefail

SOLUTION_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO="/workspace/repo"

cp "$SOLUTION_DIR"/*.go "$REPO/"
cp "$SOLUTION_DIR/go.mod" "$REPO/go.mod"

rm -rf "$REPO/fonts"
mkdir -p "$REPO/fonts"
cp "$SOLUTION_DIR"/fonts/*.flf "$REPO/fonts/"

find "$REPO" -type f -name "*.py" -delete
rm -rf "$REPO/pyfiglet"

cd "$REPO"
go build -o /tmp/figlet .
