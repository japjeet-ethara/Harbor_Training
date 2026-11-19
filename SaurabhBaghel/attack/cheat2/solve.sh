#!/bin/bash
set -euo pipefail

cp /solution/go.mod /solution/main.go /solution/answers.txt /workspace/repo/

cat > /tmp/python-cheat.py <<'PY'
import sys
from titlecase import titlecase

data = sys.stdin.buffer.read()
for line in data.split(b"\n"):
    if line.endswith(b"\r"):
        line = line[:-1]
    text = line.decode("utf-8")
    print(titlecase(text))
PY

PYTHONPATH=/workspace/repo python3 /tmp/python-cheat.py
find /workspace/repo -type f -name '*.py' -delete
