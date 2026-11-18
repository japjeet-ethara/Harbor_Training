from pathlib import Path

from titlecase import titlecase

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "titlecase-go" / "tests" / "data"

def require(path):
    if not path.is_file():
        raise SystemExit(f"abort: missing {path}")

def load(name):
    path = DATA / f"{name}.txt"
    require(path)
    with path.open(encoding="utf-8", newline="\n") as fh:
        return fh.read().split("\n")[:-1]

for prefix in ("", "hidden_"):
    src = load(prefix + "inputs")
    exp = load(prefix + "expected")
    print(prefix or "dev_", "lines:", len(src), len(exp))
    for i in (3, 400, 999, 1500, 1999):
        status = "OK  " if titlecase(src[i]) == exp[i] else "DIFF"
        print(status, i, ascii(src[i])[:70])