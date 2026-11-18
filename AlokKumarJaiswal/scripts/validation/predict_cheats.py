from pathlib import Path

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

dev_exp = load("expected")
hid_in = load("hidden_inputs")
hid_exp = load("hidden_expected")
total = max(len(dev_exp), len(hid_exp))

def reward(build, no_py, behaviour):
    return (build * 1 + no_py * 1 + 4 * behaviour) / 6

a_equal = sum(a == b for a, b in zip(dev_exp, hid_exp))
b_equal = sum(a == b for a, b in zip(hid_in, hid_exp))

rows = [
    ("A: print dev answers, keep .py", 1, 0, a_equal / total),
    ("A: print dev answers, delete .py", 1, 1, a_equal / total),
    ("B: echo input, keep .py", 1, 0, b_equal / total),
    ("B: echo input, delete .py", 1, 1, b_equal / total),
]
print("hidden lines equal: A =", a_equal, " B =", b_equal, " of", total)
for name, b, n, beh in rows:
    print(f"{name:36s} behaviour={beh:.4f} reward={reward(b, n, beh):.4f}")