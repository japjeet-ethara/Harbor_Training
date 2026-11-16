"""Isolated original pyfiglet.main invocation for killable per-case timeouts."""
import io
import json
import sys

sys.path.insert(0, sys.argv[1])
import pyfiglet

args = json.loads(sys.argv[2])
raw = io.BytesIO()
sys.stdout = io.TextIOWrapper(raw, encoding="utf-8", newline="")
sys.stderr = io.StringIO()
sys.argv = ["pyfiglet"] + args
try:
    code = pyfiglet.main()
except SystemExit as exc:
    code = exc.code
if code not in (None, 0):
    raise SystemExit(int(code))
sys.stdout = sys.__stdout__
sys.stdout.write(raw.getvalue().decode("utf-8"))
