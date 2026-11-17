"""Differential test: many more cases than the task ships, over EVERY standard font and more widths,
with answers from the original, for comparing the Go port.

Usage (from the task folder):  python dev/fuzz.py .. ../scratch [COUNT]
The first argument is the folder that holds pyfiglet and figlet-go, the second is where fuzz.jsonl is written.
"""
import importlib.util
import random
import sys
from pathlib import Path

work, out = Path(sys.argv[1]), Path(sys.argv[2])
count = int(sys.argv[3]) if len(sys.argv) > 3 else 40000
spec = importlib.util.spec_from_file_location("gen", work / "figlet-go" / "tests" / "gen.py")
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)

pyfiglet = gen.load_original()
gen.FONTS = sorted(p.stem for p in (work / "pyfiglet" / "pyfiglet" / "fonts").glob("*.flf"))
gen.WIDTHS = [7, 10, 13, 20, 33, 40, 60, 79, 80, 81, 120, 200]
rng = random.Random(20261117)
cases = gen.make_cases(pyfiglet, rng, count, set())
out.mkdir(parents=True, exist_ok=True)
gen.write_cases(out / "fuzz.jsonl", cases)
fonts = {}
for case in cases:
    args = case["args"]
    name = args[args.index("-f") + 1] if "-f" in args else "standard"
    fonts[name] = fonts.get(name, 0) + 1
print(len(cases), "cases over", len(fonts), "fonts; fewest per font:", min(fonts.values()))
