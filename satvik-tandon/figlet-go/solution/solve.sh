#!/usr/bin/env bash
set -euo pipefail
root=/workspace/repo
here="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$root/fonts"
cp "$root"/pyfiglet/fonts/{standard,slant,small,big,mini,banner,shadow,script}.flf "$root/fonts/"
cp "$here/main.go.txt" "$root/main.go"
printf 'module figlet-go\n\ngo 1.23\n' > "$root/go.mod"
find "$root" -type f -name '*.py' -delete
