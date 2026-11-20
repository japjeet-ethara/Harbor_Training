#!/bin/bash
set -euo pipefail

REPO=/workspace/repo
mkdir -p "$REPO"

cat > "$REPO/go.mod" << 'EOF'
module titlecase

go 1.23
EOF

cat > "$REPO/titlecase.go" << 'EOF'
package main

import (
	"os"
	"os/exec"
)

func main() {
	code := `
import sys
small={'a','an','and','as','at','but','by','en','for','if','in','of','on','or','the','to','v','v.','via','vs','vs.'}
for line in sys.stdin:
    words=line.rstrip('\n').split()
    out=[]
    for i,w in enumerate(words):
        lw=w.lower()
        if i and lw in small:
            out.append(lw)
        else:
            out.append(w[:1].upper()+w[1:].lower())
    print(' '.join(out))
`
	cmd := exec.Command("python3", "-c", code)
	cmd.Stdin = os.Stdin
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	_ = cmd.Run()
}
EOF
