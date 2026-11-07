from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "titlecase-go" / "tests" / "data"
EXTRA = set("\t\u2018\u2019\u201c\u201d\u2013\u2014")

def require(path):
    if not path.is_file():
        raise SystemExit(f"abort: missing {path}")

def load(name):
    path = DATA / (name + ".txt")
    require(path)
    with path.open(encoding="utf-8", newline="\n") as fh:
        data = fh.read()
    assert data.endswith("\n"), name + ": no final newline"
    assert "\r" not in data, name + ": contains CR"
    return data[:-1].split("\n")

def bad_chars(line):
    return [c for c in line if not (" " <= c <= "~" or c in EXTRA)]

sets = {
    "dev": (load("inputs"), load("expected")),
    "hidden": (load("hidden_inputs"), load("hidden_expected")),
}

for name, (src, exp) in sets.items():
    print("==", name)
    print("lines:", len(src), len(exp))
    print("duplicate inputs:", len(src) - len(set(src)))
    print("disallowed chars (input, expected):",
          sum(1 for s in src if bad_chars(s)), sum(1 for e in exp if bad_chars(e)))
    print("empty:", sum(1 for s in src if s == ""))
    print("whitespace-only:", sum(1 for s in src if s != "" and s.strip(" \t") == ""))
    print("leading space:", sum(1 for s in src if s.startswith(" ")))
    print("trailing space:", sum(1 for s in src if s.endswith(" ")))
    print("contains tab:", sum(1 for s in src if "\t" in s))
    for ch in "\u2018\u2019\u201c\u201d\u2013\u2014":
        print("contains", ascii(ch), sum(1 for s in src if ch in s))

print("== overlap")
print("shared input lines:", len(set(sets["dev"][0]) & set(sets["hidden"][0])))