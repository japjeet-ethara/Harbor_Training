from pathlib import Path
import hashlib
import json

root = Path(__file__).resolve().parents[1] / "tests/data"
files = {}
for name in ("inputs.txt", "answers.txt"):
    payload = (root / name).read_bytes()
    records = payload.split(b"\n")[:-1]
    assert payload.endswith(b"\n") and len(records) == 100000
    files[name] = {"records": len(records), "bytes": len(payload),
                   "sha256": hashlib.sha256(payload).hexdigest()}
(root / "manifest.json").write_text(
    json.dumps({"schema_version": 1, "mode": "stdlib-re", "files": files}, indent=2) + "\n",
    encoding="utf-8",
)
