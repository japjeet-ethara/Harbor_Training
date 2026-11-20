#!/bin/bash
# Build one port inside a disposable golang:1.23 container (network off).
# Mounts: /env (task's environment repo, read-only), /sol (solution dir, read-only),
#         /out (writable: receives the binary and build facts).
# Usage: bash /tools/build_port.sh <interpreter for solve.sh>
set -u
interp="$1"
mkdir -p /workspace/repo && cp -a /env/. /workspace/repo/
cd /workspace/repo
go version > /out/go-version.txt
echo "solve.sh via: $interp" > /out/build-steps.txt
"$interp" /sol/solve.sh > /out/solve.log 2>&1
echo "solve.sh exit $?" >> /out/build-steps.txt
cd /workspace/repo
go build ./... > /out/build-all.log 2>&1
echo "go build ./... exit $?" >> /out/build-steps.txt
go build -o /out/titlecase . > /out/build-bin.log 2>&1
echo "go build -o titlecase . exit $?" >> /out/build-steps.txt
echo "py files left: $(find /workspace/repo -name '*.py' | wc -l)" >> /out/build-steps.txt
# Keep a copy of the Go sources the build actually used.
mkdir -p /out/src
find /workspace/repo -maxdepth 1 -type f \( -name '*.go' -o -name 'go.mod' -o -name 'go.sum' \) -exec cp {} /out/src/ \;
( cd /out/src && sha256sum * ) > /out/src-sha256.txt
sha256sum /out/titlecase | cut -c1-64 > /out/binary-sha256.txt
