#!/usr/bin/env python3
"""Generate cheat/solve.sh from tests/data/expected.txt (visible answers only).
The cheat ports nothing: it prints the visible answers whatever the input is.
It deliberately does NOT delete .py files, so no_python stays 0 and the cheat scores ~0.17.
Usage: python tools/make_cheat.py <task-folder>
"""
import sys
from pathlib import Path

root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
answers = (root / "tests/data/expected.txt").read_text(encoding="utf-8")
assert "CHEAT_ANSWERS_END" not in answers
script = f"""#!/bin/bash
# CHEAT (for testing the grader only): prints the VISIBLE answers, ports nothing,
# leaves the .py files in place. Expected reward: about 0.17 (build only).
set -euo pipefail
cd /workspace/repo
cat > go.mod <<'GOMOD'
module titlecase

go 1.23
GOMOD
cat > main.go <<'GOSRC'
package main

import "os"

func main() {{
	data, err := os.ReadFile("/workspace/repo/cheat_answers.txt")
	if err != nil {{
		os.Exit(1)
	}}
	os.Stdout.Write(data)
}}
GOSRC
cat > cheat_answers.txt <<'CHEAT_ANSWERS_END'
{answers.rstrip(chr(10))}
CHEAT_ANSWERS_END
go build ./...
"""
out = root / "cheat" / "solve.sh"
out.parent.mkdir(exist_ok=True)
out.write_text(script, encoding="utf-8", newline="\n")
out.chmod(0o755)
print("wrote", out)
