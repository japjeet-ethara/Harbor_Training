#!/bin/bash
set -euo pipefail

CHEAT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO="/workspace/repo"

cp "$CHEAT_DIR"/main.go "$REPO/main.go"
cp "$CHEAT_DIR"/go.mod "$REPO/go.mod"
cp "$CHEAT_DIR"/visible.jsonl "$REPO/visible.jsonl"

find "$REPO" -type f -name "*.py" -delete
rm -rf "$REPO/pyfiglet"

cd "$REPO"
go build -o /tmp/figlet .
