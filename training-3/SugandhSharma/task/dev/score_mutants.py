"""Counts, for every mutant, the lines it gets wrong on the hidden set, the visible set and the big fuzz set."""
import sys
from pathlib import Path

mut = Path(sys.argv[1])
sets = {}
for label, exp in (("hidden", sys.argv[2]), ("visible", sys.argv[3]), ("fuzz", sys.argv[4])):
    sets[label] = Path(exp).read_bytes().split(b"\n")[:-1]
names = (mut / "names.txt").read_text(encoding="utf-8").split()
survivors, equivalent, failed_build = [], [], []
print(f"{'mutant':44s} hidden visible   fuzz")
for name in names:
    row = []
    for label in ("hidden", "visible", "fuzz"):
        f = mut / f"{name}.{label}.out"
        if not f.exists():
            row.append(None)
            continue
        got = f.read_bytes().split(b"\n")
        exp = sets[label]
        row.append(sum(1 for i, e in enumerate(exp) if i >= len(got) or got[i] != e))
    if row[0] is None:
        failed_build.append(name)
        continue
    flag = ""
    if row[0] == 0 and row[2] == 0:
        equivalent.append(name); flag = "  (same on 200k too: no visible effect)"
    elif row[0] == 0:
        survivors.append(name); flag = "  <-- NOT CAUGHT by the hidden set"
    print(f"{name:44s} {row[0]:6d} {row[1]:7d} {row[2]:6d}{flag}")
print()
print("did not build:", failed_build)
print("not caught by the hidden set:", survivors)
print("no visible effect anywhere:", equivalent)
