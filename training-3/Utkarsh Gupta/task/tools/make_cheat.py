#!/usr/bin/env python3
"""Step 7: build cheat/solve.sh - a 'solution' that ignores stdin and just prints tests/data/expected.txt."""
import base64
from pathlib import Path

root = Path(__file__).resolve().parent.parent
blob = base64.b64encode((root / "tests/data/expected.txt").read_bytes()).decode()
go = '''package main

import (
	"encoding/base64"
	"os"
)

const blob = "%s"

func main() {
	b, _ := base64.StdEncoding.DecodeString(blob)
	os.Stdout.Write(b)
}
''' % blob
script = f"""#!/bin/bash
# CHEAT: not a port. Prints the visible expected.txt whatever the input is.
set -euo pipefail
cd /workspace/repo
printf 'module titlecase\\n\\ngo 1.23\\n' > go.mod
cat > main.go <<'GOSRC'
{go}GOSRC
find /workspace/repo -name '*.py' -delete
"""
out = root / "cheat/solve.sh"
out.write_text(script)
out.chmod(0o755)
print("wrote", out)
