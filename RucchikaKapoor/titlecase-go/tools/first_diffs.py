#!/usr/bin/env python3
"""Step 6 helper: print the first N lines where the Go program differs from the expected answers.

usage: python tools/first_diffs.py <dir-with-go.mod> tests/data/inputs.txt tests/data/expected.txt [N]
"""
import subprocess
import sys
from pathlib import Path

go_dir, inp, exp = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
limit = int(sys.argv[4]) if len(sys.argv) > 4 else 10
subprocess.run(["go", "build", "-o", "/tmp/tc_bin", "."], cwd=go_dir, check=True)
out = subprocess.run(["/tmp/tc_bin"], input=inp.read_bytes(), capture_output=True, check=True).stdout
ins = inp.read_text(encoding="utf-8").split("\n")
exps = exp.read_text(encoding="utf-8").split("\n")
outs = out.decode("utf-8", "replace").split("\n")
shown = bad = 0
for i, (a, e, g) in enumerate(zip(ins, exps, outs), 1):
    if e != g:
        bad += 1
        if shown < limit:
            shown += 1
            print(f"line {i}\n  input   : {a!r}\n  expected: {e!r}\n  actual  : {g!r}")
print(f"{bad} differing lines out of {len(ins) - 1}")
