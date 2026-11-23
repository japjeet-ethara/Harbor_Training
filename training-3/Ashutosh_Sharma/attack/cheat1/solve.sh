#!/usr/bin/env bash
set -e
cd /workspace/repo
find . -name "*.py" -delete
[ -f go.mod ] || go mod init titlecase
cat << 'EOF' > main.go
package main

func main() {}
EOF