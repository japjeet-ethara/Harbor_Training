"""Shows the first lines where the Go program's output differs from the frozen answers.

Usage (from the task folder):  python dev/compare.py dev/actual.txt [tests/data/inputs.txt tests/data/expected.txt]
"""
import sys
from pathlib import Path

actual = Path(sys.argv[1]).read_bytes().split(b"\n")
inputs = Path(sys.argv[2] if len(sys.argv) > 2 else "tests/data/inputs.txt").read_bytes().split(b"\n")[:-1]
expected = Path(sys.argv[3] if len(sys.argv) > 3 else "tests/data/expected.txt").read_bytes().split(b"\n")[:-1]
wrong = [i for i, want in enumerate(expected) if i >= len(actual) or actual[i] != want]
print(f"{len(expected) - len(wrong)} of {len(expected)} lines match; {len(wrong)} differ")
for i in wrong[:10]:
    got = actual[i] if i < len(actual) else b"<no line>"
    print(f"line {i + 1}\n  input:    {inputs[i]!r}\n  expected: {expected[i]!r}\n  actual:   {got!r}")
sys.exit(1 if wrong else 0)
