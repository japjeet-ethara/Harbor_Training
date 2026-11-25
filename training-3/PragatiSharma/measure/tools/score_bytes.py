"""Independent byte-level cross-check of compare.py (writes nothing).

Usage: python -I score_bytes.py <suite_dir> <got.txt>
Splits on LF only, compares raw bytes, and reports record counts.
"""
import hashlib
import sys


def records(data):
    if data.endswith(b"\n"):
        data = data[:-1]
    return data.split(b"\n") if data else []


suite, got_path = sys.argv[1], sys.argv[2]
want = records(open(f"{suite}/answers.txt", "rb").read())
inputs = records(open(f"{suite}/inputs.txt", "rb").read())
raw = open(got_path, "rb").read()
got = records(raw)
n = min(len(want), len(got))
wrong = sum(1 for i in range(n) if got[i] != want[i]) + abs(len(want) - len(got))
LF, CR = bytes([10]), bytes([13])
print(f"inputs={len(inputs)} answers={len(want)} output_records={len(got)} "
      f"LF={raw.count(LF)} CR={raw.count(CR)} ends_with_LF={raw.endswith(LF)} "
      f"correct={len(want) - wrong} wrong={wrong} "
      f"got_sha256={hashlib.sha256(raw).hexdigest()}")
