from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
root = ROOT / "titlecase-go"
if not root.is_dir():
    raise SystemExit(f"abort: missing {root}")
for p in sorted(root.rglob("*")):
    if p.is_file() and "repo" not in p.parts and "data" not in p.parts:
        data = p.read_bytes()
        print("CRLF" if b"\r\n" in data else "ok  ", p.relative_to(ROOT))