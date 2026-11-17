#!/bin/bash
# Reference solution. The Go port lives next to this script (go.mod and the .go files).
# This script puts it into the repository, keeps the fonts inside the repository, and removes the Python code.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
cd /workspace/repo

# The fonts the program builds in: the .flf files the original loads, moved to ./fonts.
mkdir -p fonts
cp pyfiglet/fonts/*.flf fonts/

cp "$here"/go.mod "$here"/*.go .

# The Python program goes: every .py file, and the package folder that held it and the old font folders.
find . -name '*.py' -delete
rm -rf pyfiglet
find . -name '__pycache__' -type d -prune -exec rm -rf {} +
find . -type d -empty -delete
