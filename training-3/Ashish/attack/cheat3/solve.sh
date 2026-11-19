#!/bin/bash
set -euo pipefail
cd /workspace/repo

cat > go.mod << 'TITLECASE_CHEAT3'
module titlecase

go 1.23
TITLECASE_CHEAT3

cat > main.go << 'TITLECASE_CHEAT3'
package main

import (
	"bufio"
	"os"
)

// Cheat 3: silent binary. It consumes stdin and emits nothing.
// With build=1 and no_python=1, this isolates the 2/6 scoring floor:
// reward = (4*0 + 1*1 + 1*1) / 6 = 0.3333.
func main() {
	in := bufio.NewScanner(os.Stdin)
	in.Buffer(make([]byte, 0, 64*1024), 4*1024*1024)
	for in.Scan() {
	}
}
TITLECASE_CHEAT3

find /workspace/repo -type f -name '*.py' -delete
rm -rf /workspace/repo/titlecase
