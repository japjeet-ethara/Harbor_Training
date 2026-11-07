#!/usr/bin/env python3
"""Generate the test titles and freeze the expected answers.

    python tests/gen.py

Writes four files into tests/data/:

    inputs.txt          2000 titles   (visible set, used while developing the oracle)
    expected.txt        their answers
    hidden_inputs.txt   2000 different titles (the set the verifier grades on)
    hidden_expected.txt their answers

The answers are never written by hand: every one comes from running the ORIGINAL
python-titlecase (the pinned snapshot in environment/python-titlecase) with the
optional `regex` package installed. Output is deterministic: random.seed(1).
"""
import hashlib
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent / "environment" / "python-titlecase"
DATA = HERE / "data"
N = 2000

# The snapshot is python-titlecase 2.4.1, commit 42f43e2de55bf003b286c6f8e8d8b2d26676a167.
PINNED_SHA256 = "a3d0b99857c7672b9a13ec9df54aa187082be7d39b202dc0511e67e6f7873ef0"


def load_original():
    source = REPO / "titlecase" / "__init__.py"
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    if digest != PINNED_SHA256:
        sys.exit(f"{source} is not the pinned snapshot (sha256 {digest})")
    sys.path.insert(0, str(REPO))
    # A __pycache__ folder here would end up in the agent's image.
    sys.dont_write_bytecode = True
    import titlecase as module

    if not module.REGEX_AVAILABLE:
        sys.exit("install the `regex` package: the reference behaviour is the one with it")
    return module.titlecase


SMALL = "a an and as at but by en for if in of on or the to v v. via vs vs.".split()

PLAIN = """lord rings war peace time mice men cat dog music face dance title string apple deal
problem probe trick plane edit line force case thing spool jobs thoughts permissions voodoo
caps name machine great young restless mix space characters summer winter night morning river
mountain garden kitchen window letter story history future science market company report
guide rules world people money power light water fire earth house street city country
love death life dream secret return rise fall last first new old little big long short
good bad best worst how why what when where who is are was be been do does did not with
from into over under after before about against between through without within you your
we our they their it its this that these those can will should must may might""".split()

CONSONANT = "cnn tv st nd hmm pfft dvd html css mph xyz nth rhythm my sky gym bbc fbi ps pdf tsk brr shh fm".split()

MIXED = """iTunes iPhone eBay OmniFocus YouTube GitHub McCarthy MacBook AT&T AT&T's Q&A SEC's NASA
FBI PhD LaTeX macOS JavaScript DeLorean kHz mRNA USA UK""".split()

NAMES = """o'reilly o'grange's d'angelo l'grange o'neil O'GranGe l'GranGe o‘brien d'artagnan's
o'as' o's' o'3d l' d' o'connor, o'hara's mctavish mcdonalds macdonalds mcfoo-bar mccay-mcbut-mcdo
mcthe mcby mc mac mc1 mc-x mcx mca mr mrs ms mss dr mr. mrs. dr. ms. drs""".split()

DOTTED = """example.com del.icio.us http://foo.com https://example.org/a-b e.g. i.e. u.s.a. node.js
v.x vs.x in.a d.c. a.b a.bc. u.s. p.m. v1.2 3.5mm x.1 1.x a.m www.site.org/and/or file.txt mr.x
st. no.9 to.the of.a""".split()

SLASHED = """and/or word/word him/her tcp/ip a/b/c x//y /x x/ the/a mcdonalds/mcby
o'melveny/o'doyle 24/7 yes/no/maybe of/the either/or""".split()

HYPHEN = """end-to-end state-of-the-art e-mail two-not-three x-ray to-do a-b the-the five-and - --
-a a- mother-in-law re-entry top-of-the-line t-shirt by-the-way up-to-date wi-fi in-flight""".split()

DIGITS = "34th 3rd 2nd 5th 2lmc 7 1984 3d 100% $5 no.1 4x4 #1 1st b2b mp3 r2d2 9to5".split()

PARENS = "(u)rware vapo(u)rware (the) (a of) [and] {or} (mc) (cnn) (o'reilly)".split()

ACCENTED = """niño arrivé café über ýæ ñø façade jalapeño señor crème brûlée naïve æon øre
Ångström élan smörgåsbord piñata déjà vu""".split()

POOLS = [
    (SMALL, 26), (PLAIN, 36), (CONSONANT, 5), (MIXED, 5), (NAMES, 6), (DOTTED, 5),
    (SLASHED, 4), (HYPHEN, 5), (DIGITS, 3), (PARENS, 2), (ACCENTED, 3),
]
POOL_ITEMS = [p for p, _ in POOLS]
POOL_WEIGHTS = [w for _, w in POOLS]

OPENERS = ["'", '"', "‘", "“", "(", "[", "*", "_", "#", "@", "’", "”", "¿"]
CLOSERS = ["'", '"', "’", "”", ")", "]", ",", ".", ":", ";", "?", "!", "...", "?!", "'s", "’s", "%"]

# Mostly a single space; sometimes a sub-phrase break or an unusual space character.
SEPARATORS = (
    [" "] * 60
    + [": ", " - ", " — ", " – ", "; ", "? ", "! ", ". ", ", ", " ― ", " ‒ "] * 2
    + ["  ", "\t", " ", " ", " "]
)

# Whole lines that exercise a specific rule or a known trap.
FIXED = [
    "the lord of the rings",
    "of mice and men",
    "something to be afraid of",
    "'by the way, small word at the start but within quotes.'",
    "starting sub-phrase with a small word: a trick, perhaps?",
    'sub-phrase with a small word in quotes: "a trick, perhaps?"',
    "snakes on a plane - the tv edit - the famous line",
    "episode 7 — the force awakens",
    "EPISODE 7 — THE FORCE AWAKENS",
    "THE CASE OF X ≤ 7",
    "the case of X ≤ 7",
    "WASHINGTON, D.C. SHOULD BE FIXED BUT MIGHT BE A PROBLEM",
    "THIS IS ALL CAPS AND SHOULD BE ADDRESSED",
    "MR SMITH GOES TO NASA",
    "FOO BAR 5TH ST",
    "mr mrs ms mss dr dr , mr. and mrs. person",
    "x. v. a b",
    "vs. a b: vs. a",
    "v.x is first",
    "in.a",
    "to-do list to-do",
    "'AND then",
    " the cat",
    "the cat of ",
    "two  spaces",
    "a mix of\tdifferent space characters",
    "this is just an example.com",
    "this is http://foo.com/and/or",
    "words with all consonants like cnn are acronyms",
    "mac mc MAC MC machine",
    "mcfoo-bar, MCFOO-BAR, McFoo-bar, McFoo-Bar, mcfoo-mcbar, foo-mcbar",
    "l'grange L'grange l'Grange L'GRANGE",
    "o'grange's O'grange's o'Grange's O'GRANGE'S",
    "2lmc spool: 'gruber on OmniFocus and vapo(u)rware'",
    "EL NIÑO A ARRIVÉ HIER",
    "ýæ ñø",
    "‘quote’ a great",
    "“YOUNG AND RESTLESS”",
    "release notes for v1.2 and 3.5mm jacks",
    "a",
    "THE",
    "of?",
    '"nothing to be afraid of?"',
    "at&t at&t",
    "and",
    "I",
]

FORBIDDEN = set("\r\n\x0b\x0c\x1c\x1d\x1e\x85  ")


def restyle(word):
    """Occasionally change the capitalisation of one word."""
    r = random.random()
    if r < 0.80:
        return word
    if r < 0.88:
        return word.upper()
    if r < 0.95:
        return word.capitalize()
    return "".join(c.upper() if random.random() < 0.4 else c for c in word)


def token():
    pool = random.choices(POOL_ITEMS, weights=POOL_WEIGHTS)[0]
    word = restyle(random.choice(pool))
    if random.random() < 0.07:
        word = random.choice(OPENERS) + word
    if random.random() < 0.12:
        word = word + random.choice(CLOSERS)
    return word


def title():
    count = random.choices([1, 2, 3, 4, 5, 6, 7, 8, 9], weights=[4, 8, 12, 16, 18, 16, 12, 8, 6])[0]
    parts = []
    for i in range(count):
        parts.append(token())
        if i < count - 1:
            parts.append(random.choice(SEPARATORS))
    line = "".join(parts)
    r = random.random()
    if r < 0.14:
        line = line.upper()
    elif r < 0.17:
        line = " " + line
    elif r < 0.20:
        line = line + " "
    return line


def main():
    titlecase = load_original()
    random.seed(1)

    lines = list(FIXED)
    seen = set(lines)
    while len(lines) < 2 * N:
        line = title()
        if line in seen or not line or FORBIDDEN & set(line):
            continue
        seen.add(line)
        lines.append(line)
    random.shuffle(lines)

    DATA.mkdir(exist_ok=True)
    for name, chunk in (("", lines[:N]), ("hidden_", lines[N:])):
        answers = [titlecase(line) for line in chunk]
        assert all("\n" not in a and "\r" not in a for a in answers)
        for filename, rows in ((f"{name}inputs.txt", chunk), (f"{name}expected.txt", answers)):
            with open(DATA / filename, "w", encoding="utf-8", newline="\n") as f:
                f.write("".join(row + "\n" for row in rows))
        print(f"wrote {len(chunk)} titles to tests/data/{name}inputs.txt and {name}expected.txt")


if __name__ == "__main__":
    main()
