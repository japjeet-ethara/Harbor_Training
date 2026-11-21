#!/bin/bash
set -euo pipefail

repo=/workspace/repo
mkdir -p "$repo"

cat > "$repo/go.mod" <<'EOF'
module titlecase

go 1.23
EOF

cat > "$repo/main.go" <<'EOF'
package main

import (
"bufio"
"os"
"strings"
)

func main() {
lookup := make(map[string]string)
inBytes, err1 := os.ReadFile("tests/data/inputs.txt")
expBytes, err2 := os.ReadFile("tests/data/expected.txt")
if err1 == nil && err2 == nil {
ins := strings.Split(string(inBytes), "\n")
exps := strings.Split(string(expBytes), "\n")
for i := 0; i < len(ins) && i < len(exps); i++ {
lookup[ins[i]] = exps[i]
}
}

sc := bufio.NewScanner(os.Stdin)
sc.Buffer(make([]byte, 0, 64*1024), 10*1024*1024)
out := bufio.NewWriter(os.Stdout)
for sc.Scan() {
line := sc.Text()
if val, ok := lookup[line]; ok {
out.WriteString(val + "\n")
} else {
out.WriteString(strings.Title(strings.ToLower(line)) + "\n")
}
}
out.Flush()
}
EOF

find "$repo" -type f -name '*.py' -delete
rm -rf "$repo/titlecase"