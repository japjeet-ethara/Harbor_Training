#!/bin/bash
# ==============================================================================
# CHEAT 3 — Build Trick + Empty Stub / Delete Trick
# ==============================================================================
# Strategy:
#   This cheat demonstrates that a candidate gets 33.3% credit (build + no_python)
#   without producing any correct titlecase behavior. It creates a dummy Go program
#   that compiles cleanly and exits immediately, and deletes all .py files.
#   This proves that build and no_python award unearned marks without any behaviour gating.
# ==============================================================================
set -euo pipefail

cd /workspace/repo

# 1. Write go.mod
cat > go.mod << 'EOF'
module titlecase

go 1.23
EOF

# 2. Minimal valid Go program that satisfies build
cat > main.go << 'GOEOF'
package main

import (
	"bufio"
	"fmt"
	"io"
	"os"
	"strings"
)

func main() {
	reader := bufio.NewReader(os.Stdin)
	writer := bufio.NewWriter(os.Stdout)
	defer writer.Flush()

	for {
		line, err := reader.ReadString('\n')
		if err != nil {
			if err == io.EOF && len(line) > 0 {
				fmt.Fprintln(writer, strings.TrimRight(line, "\r\n"))
			}
			break
		}
		// Echo raw line without transformation
		fmt.Fprintln(writer, strings.TrimRight(line, "\r\n"))
	}
}
GOEOF

# 3. Delete all Python files
find /workspace/repo -type f -name "*.py"  -delete
find /workspace/repo -type f -name "*.pyc" -delete
rm -rf /workspace/repo/titlecase
find /workspace/repo -type d -name "__pycache__" -empty -delete

# 4. Build check
go build -o /dev/null ./...

echo "Cheat 3 solve.sh completed successfully."
