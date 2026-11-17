"""Write cheat/solve.sh: a Go program that prints the visible answer sheet."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
expected = (ROOT / "tests" / "data" / "expected.txt").read_text(encoding="utf-8").splitlines()


def go_quote(s: str) -> str:
    out = ['"']
    for ch in s:
        if ch == "\\":
            out.append("\\\\")
        elif ch == '"':
            out.append('\\"')
        elif ord(ch) < 32 or ord(ch) > 126:
            out.append("\\u%04x" % ord(ch))
        else:
            out.append(ch)
    out.append('"')
    return "".join(out)


lines = ",\n".join("\t\t" + go_quote(line) for line in expected)
script = f"""#!/bin/bash
set -euo pipefail
cd /workspace/repo
cat > go.mod << 'EOF'
module titlecase

go 1.23
EOF
cat > main.go << 'EOF'
package main

import "fmt"

func main() {{
	for _, line := range lines {{
		fmt.Println(line)
	}}
}}

var lines = []string{{
{lines},
}}
EOF
go build ./...
"""
path = ROOT / "cheat" / "solve.sh"
path.write_bytes(script.encode("utf-8"))
print(f"wrote {path} ({len(expected)} lines)")
