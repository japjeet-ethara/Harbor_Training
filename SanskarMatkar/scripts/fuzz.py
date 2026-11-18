#!/usr/bin/env python3
"""Fuzz a built Go binary against the original:  python3 scripts/fuzz.py <seed> <path-to-binary>"""
import sys, random, subprocess
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parents[1] / 'tests'))
import gen   # reuses the generator + the stdlib-re reference
rng = random.Random(int(sys.argv[1]))
lines = [gen.make_title(rng) for _ in range(100000)]
alphabet = list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") + \
    list("!\"#$%&'()*+,-./:;?@[\\]_`{|}~ \t") + list("“”‘’–—‒―…  éÉñÑüç") + \
    ["a","an","the","of","v.","vs.","mc","Mc","MC","o'","d'","l'","mr","dr","/","-","//",". ",": ","  "]*3
for _ in range(50000):
    lines.append("".join(rng.choice(alphabet) for _ in range(rng.randint(0, 40))))
lines = [l for l in lines if "\n" not in l and "\r" not in l]
exp = [gen.titlecase(l) for l in lines]
data = "".join(l + "\n" for l in lines).encode()
got = subprocess.run([sys.argv[2]], input=data, capture_output=True).stdout.decode().split("\n")[:-1]
bad = [(l, e, g) for l, e, g in zip(lines, exp, got) if e != g]
print(f"seed {sys.argv[1]}: {len(lines)-len(bad)}/{len(lines)} match, out lines {len(got)}")
for l, e, g in bad[:15]: print(" in ", repr(l), "\n exp", repr(e), "\n got", repr(g))
