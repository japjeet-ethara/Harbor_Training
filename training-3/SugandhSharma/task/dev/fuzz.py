"""Differential test: about 200,000 extra titles, with answers from the original, for comparing the Go port.

Usage (from the task folder):  python dev/fuzz.py .. ../scratch
The first argument is the folder that holds python-titlecase and titlecase-go, the second is where to write.
"""
import importlib.util, random, sys
from pathlib import Path

work = Path(sys.argv[1]); out = Path(sys.argv[2])
sys.dont_write_bytecode = True
sys.modules["regex"] = None
sys.path.insert(0, str(work / "python-titlecase"))
import titlecase as original
assert original.REGEX_AVAILABLE is False
spec = importlib.util.spec_from_file_location("gen", work / "titlecase-go" / "tests" / "gen.py")
gen = importlib.util.module_from_spec(spec); spec.loader.exec_module(gen)

rng = random.Random(20261117)
titles = set()
while len(titles) < 100000:                       # the task's own generator, other random draws
    titles.add(gen.one_title(rng))
for _ in range(40):                               # the built-on-purpose punctuation titles, other random draws
    titles.update(t for t in gen.coverage_titles(rng) if set(t) <= gen.ALLOWED)
ALLOWED = sorted(gen.ALLOWED)
TOKENS = gen.SMALL + gen.TRICKY + gen.PLAIN[:40] + ["Mc", "MC", "mc", "d'", "o'", "l'", "'s", "s'", ".", "..", "/", "//", "-", "_",
          ":", ": ", ". ", "; ", "? ", "! ", "- ", "\u2014 ", "\u2013 ", "\u2012 ", "\u2015 ", " ", "  ", "\t", "'", "\u2018", "\u2019",
          "\u201c", "\u201d", "(", ")", "[", "]", "<", ">", "&", "@", "#", "1", "22", "A", "B", "x", "y", "Y", "st", "nd", "th"]
while len(titles) < 200000:                       # token soup and raw character soup
    if rng.random() < 0.7:
        t = "".join(rng.choice(TOKENS) if rng.random() < 0.8 else rng.choice(ALLOWED) for _ in range(rng.randint(1, 8)))
        if rng.random() < 0.3:
            t = t.upper()
        elif rng.random() < 0.2:
            t = "".join(c.upper() if rng.random() < 0.4 else c.lower() for c in t)
    else:
        t = "".join(rng.choice(ALLOWED) for _ in range(rng.randint(1, 14)))
    if set(t) <= gen.ALLOWED:
        titles.add(t)
titles = sorted(titles)
rng.shuffle(titles)
answers = [original.titlecase(t) for t in titles]
keep = [i for i, a in enumerate(answers) if "\n" not in a and "\r" not in a]
gen.write_lines(out / "fuzz_inputs.txt", [titles[i] for i in keep])
gen.write_lines(out / "fuzz_expected.txt", [answers[i] for i in keep])
print("lines written:", len(keep), "of", len(titles))
