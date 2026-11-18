#!/usr/bin/env python3
"""Step 6 helper: run a Go titlecase binary on an inputs file and print the
first N lines that differ from the expected file (input / expected / actual).

Usage: python3 tools/diff_first10.py BINARY [INPUTS] [EXPECTED] [N]
Defaults: tests/data/inputs.txt tests/data/expected.txt 10
"""
import os
import subprocess
import sys

here = os.path.dirname(os.path.abspath(__file__))
binary = sys.argv[1]
inputs = sys.argv[2] if len(sys.argv) > 2 else os.path.join(here, "..", "tests", "data", "inputs.txt")
expected = sys.argv[3] if len(sys.argv) > 3 else os.path.join(here, "..", "tests", "data", "expected.txt")
limit = int(sys.argv[4]) if len(sys.argv) > 4 else 10

data = open(inputs, "rb").read()
out = subprocess.run([binary], input=data, capture_output=True, timeout=120).stdout
ins = data.decode("utf-8").split("\n")[:-1]
exp = open(expected, "rb").read().decode("utf-8").split("\n")[:-1]
act = out.decode("utf-8", "replace").split("\n")
if act and act[-1] == "":
    act.pop()
bad = 0
for i, (a, b) in enumerate(zip(ins, exp)):
    got = act[i] if i < len(act) else "<missing>"
    if got != b:
        bad += 1
        if bad <= limit:
            print(f"line {i + 1}\n  input:    {a!r}\n  expected: {b!r}\n  actual:   {got!r}")
print(f"{bad} of {len(exp)} lines differ ({len(exp) - bad} match)")
sys.exit(1 if bad else 0)
