#!/bin/sh
set -eu
cd /workspace/repo
find . -type f -name '*.py' -delete
rmdir titlecase
cat > go.mod <<'EOF'
module titlecase

go 1.23
EOF
cat > main.go <<'EOF'
package main

import ("io"; "os")

func main() {
    if _, err := io.Copy(os.Stdout, os.Stdin); err != nil { panic(err) }
}
EOF
