import hashlib
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "environment", "repo"))
sys.path.insert(0, REPO)
import titlecase as tc
from titlecase import titlecase

engine = "regex" if getattr(tc, "REGEX_AVAILABLE", False) else "re"
print("reference engine:", engine)
if engine != "regex":
    sys.exit("ERROR: install regex first: python -m pip install regex")

TRICKY = [
    "the lord of the rings", "q&a with steve jobs: 'that's what happens in technology'",
    "what is at&t's problem?", "words with all consonants like cnn are acronyms",
    "this v that", "this v. that", "this vs. that", "the sec's apple probe: what you need to know",
    "small word at end is nothing to be afraid of",
    "starting sub-phrase with a small word: a trick, perhaps?",
    "em dash delimited sub-phrase with a small word in quotes — 'a trick, perhaps?'",
    "episode 7 – the force awakens", "the case of x ≤ 7", "this is just an example.com",
    "this is something listed on del.icio.us", "itunes should be unmolested",
    "o'reilly should be untouched", "my name is o'reilly", "l'grange l'grange l'Grange",
    "o'grange's O'grange's", "o'melveny/o'doyle o'melveny/O'doyle",
    "washington, d.c. should be fixed but might be a problem",
    "THIS IS ALL CAPS AND SHOULD BE ADDRESSED", "mr mctavish went to macdonalds",
    "mac mc MAC MC machine", "mccay-mcbut-mcdo mcdonalds/mcby",
    "mcfoo-bar, MCFOO-BAR, McFoo-bar, mcfoo-mcbar, foo-mcbar",
    "oblon, spivak, mcclelland, maier & neustadt",
    "Mr mr Mrs Ms Mss Dr dr , Mr. and Mrs. Person",
    "el niño a arrivé hier", "EL NIÑO A ARRIVÉ HIER", "yea no", "YEA NO", "ýæ ñø", "ÝÆ ÑØ",
    "a-b end-to-end two-not-three/three-by-four/five-and", "34th 3rd 2nd", "FOO BAR 5TH ST",
    "2lmc Spool: 'gruber on OmniFocus and vapo(u)rware'", "this is http://foo.com",
    "‘QUOTE’ A GREAT", "“YOUNG AND RESTLESS”", "a mix of\tdifferent space characters",
    "the lord of the rings and the fellowship of the ring", "a tale of two cities",
    "what to do when the going gets tough", "to be or not to be",
]
WORDS = ["apple", "banana", "cherry", "date", "elderberry", "fig", "grape", "honeydew", "kiwi",
         "lemon", "mango", "nectarine", "orange", "papaya", "quince", "raspberry", "tangerine"]


def make(rng):
    if rng.random() < 0.45:
        return rng.choice(TRICKY)
    w = [rng.choice(WORDS) for _ in range(rng.randint(2, 6))]
    for i in range(len(w)):
        r = rng.random()
        if r < 0.25:
            w[i] = w[i].upper()
        elif r < 0.5:
            w[i] = w[i].capitalize()
    return " ".join(w)


def clean(s):
    return s.replace("\r", " ").replace("\n", " ")


rng = random.Random(1)
visible, hidden, seen = [], [], set()
while len(visible) < 2000:
    s = clean(make(rng))
    if s and s not in seen:
        seen.add(s)
        visible.append(s)
while len(hidden) < 2000:
    s = clean(make(rng))
    if s and s not in seen:
        seen.add(s)
        hidden.append(s)

out = os.path.join(HERE, "data")
os.makedirs(out, exist_ok=True)
for name, data, hashname in (("inputs", visible, "expected.sha256.txt"),
                             ("hidden_inputs", hidden, "answers.sha256.txt")):
    with open(os.path.join(out, name + ".txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(data) + "\n")
    exp = [clean(titlecase(s)) for s in data]
    hashes = [hashlib.sha256(e.encode("utf-8")).hexdigest() for e in exp]
    with open(os.path.join(out, hashname), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(hashes) + "\n")

print("visible:", len(visible), "hidden:", len(hidden), "overlap:", len(set(visible) & set(hidden)))
