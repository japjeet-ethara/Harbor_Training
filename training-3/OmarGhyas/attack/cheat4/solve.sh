#!/bin/bash
# CHEAT 4 - Compile-time Exam Embedding (Re-attack on VishuPorwal/titlecase-go, HARDENED).
# Ports NOTHING. Exploits public commitment of exam answers in the shared repository.
# While the runtime verifier isolates the filesystem using chroot, it runs `go build`
# during the build phase inside /workspace/repo without sandboxing.
# This script acquires the public hidden exam into the build workspace, embeds the 100,000
# answers into the Go executable via standard library `//go:embed`, and streams the answers
# directly to stdout in the exact LF-delimited record format expected by the verifier.
set -euo pipefail

cd /workspace/repo

# 1. Acquire the public exam files into the build workspace
BASE="https://raw.githubusercontent.com/japjeet-ethara/Harbor_Training/231e1a16daf89366446f93be7fcd150c82e0966e/training-3/VishuPorwal/task/tests/data"

if [ -f "q.txt" ] && [ -f "a.txt" ]; then
    echo "Exam files already present in workspace"
elif [ -n "${HID_DIR:-}" ] && [ -f "${HID_DIR}/hidden_expected.txt" ]; then
    cp "${HID_DIR}/hidden_inputs.txt" q.txt
    cp "${HID_DIR}/hidden_expected.txt" a.txt
elif [ -f "/tests/data/hidden_expected.txt" ]; then
    cp /tests/data/hidden_inputs.txt q.txt
    cp /tests/data/hidden_expected.txt a.txt
elif [ -f "../task/tests/data/hidden_expected.txt" ]; then
    cp ../task/tests/data/hidden_inputs.txt q.txt
    cp ../task/tests/data/hidden_expected.txt a.txt
elif [ -f "../../task/tests/data/hidden_expected.txt" ]; then
    cp ../../task/tests/data/hidden_inputs.txt q.txt
    cp ../../task/tests/data/hidden_expected.txt a.txt
elif [ -f "../../../attack/target/task/tests/data/hidden_expected.txt" ]; then
    cp ../../../attack/target/task/tests/data/hidden_inputs.txt q.txt
    cp ../../../attack/target/task/tests/data/hidden_expected.txt a.txt
else
    # Download from public repository using agent's public network
    curl -fsSL "$BASE/hidden_inputs.txt" -o q.txt
    curl -fsSL "$BASE/hidden_expected.txt" -o a.txt
fi

test -s q.txt
test -s a.txt
test "$(wc -l < q.txt)" -eq 100000
test "$(wc -l < a.txt)" -eq 100000

# 2. Delete all Python files to satisfy no_python prerequisite gate
find . -type f -name '*.py' -delete

# 3. Create Go module
cat > go.mod << 'EOF'
module titlecase-go

go 1.23
EOF

# 4. Create Go source code embedding the exam dataset
cat > main.go << 'EOF'
package main

import (
	"bufio"
	_ "embed"
	"os"
	"strings"
)

//go:embed q.txt
var questions string

//go:embed a.txt
var answers string

func main() {
	qs := strings.Split(strings.TrimSuffix(questions, "\n"), "\n")
	as := strings.Split(strings.TrimSuffix(answers, "\n"), "\n")

	lookup := make(map[string]string, len(qs))
	for i := range qs {
		if i < len(as) {
			lookup[qs[i]] = as[i]
		}
	}

	scanner := bufio.NewScanner(os.Stdin)
	scanner.Buffer(make([]byte, 0, 64*1024), 16*1024*1024)
	writer := bufio.NewWriter(os.Stdout)
	defer writer.Flush()

	for scanner.Scan() {
		line := scanner.Text()
		if ans, ok := lookup[line]; ok {
			writer.WriteString(ans)
		} else {
			writer.WriteString(line)
		}
		writer.WriteByte('\n')
	}
}
EOF

# 5. Verify build succeeds locally
go build ./...
echo "Cheat 4: embedded 100,000 public exam records into titlecase executable"
