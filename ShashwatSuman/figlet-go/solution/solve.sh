#!/bin/bash
# Reference solution (the oracle): install the Go port of pyfiglet, embed the
# standard fonts, then remove every .py file. Runs as user "player".
set -euo pipefail

cd /workspace/repo

cat > go.mod <<'EOF'
module figlet

go 1.23
EOF

cp /solution/figlet.go ./figlet.go

# The fonts move to ./fonts (inside the repository) and are embedded with
# go:embed, so the binary works from any working directory.
mkdir -p fonts
cp pyfiglet/fonts/*.flf fonts/

# No .py files may be left anywhere in the repository.
find . -name '*.py' -type f -delete
find . -name '__pycache__' -type d -prune -exec rm -rf {} +

go build -o /tmp/figlet .
/tmp/figlet -f slant ok
