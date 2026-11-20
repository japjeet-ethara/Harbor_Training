import os, random, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.abspath(os.path.join(HERE, "..", "..", "python-titlecase"))
sys.path.insert(0, SRC)
import titlecase as tcmod
if not tcmod.REGEX_AVAILABLE:
    sys.exit("ERROR: the regex module is not installed (pip install regex)")
from titlecase import titlecase

random.seed(1)
N = 2000

SMALL = "a an and as at but by en for if in of on or the to v v. via vs vs.".split()
NORMAL = ("lord rings hello world movie guide report night story house river garden summer "
          "winter learning machine design review history future city music dream power journey "
          "secret letters shadow ocean market science language travel kitchen mountain").split()
TRICKY = (
    # all-consonant acronyms and short words
    ["nbc", "cnn", "tv", "st", "xyz", "bbc", "fbi", "cd", "mr", "mrs", "ms", "dr", "Dr", "MRS",
     "hmm", "rhythm", "nth", "pst", "tsk", "ssh"]
    # mixed case / Mc / Mac
    + ["iPhone", "eBay", "McDonald", "mcdonald", "MacBook", "macdonald", "mcdonald's", "MCDONALD",
       "YouTube", "PhD", "iOS", "NASA", "Nasa", "pH", "LaTeX"]
    # inline periods, domains, versions
    + ["example.com", "a.b", "www.site.org", "node.js", "e.g.", "i.e.", "3.14", "v1.2", "u.s."]
    # apostrophes
    + ["o'brien", "d'artagnan", "l'oeil", "d'Arc", "O'NEIL", "l'amour", "o'clock", "don't",
       "it's", "rock'n'roll", "d'", "'tis"]
    # slashes
    + ["input/output", "and/or", "a/b", "http://x.com", "s/he", "24/7", "either/or/neither", "the/a"]
    # hyphens
    + ["state-of-the-art", "well-known", "x-ray", "re-enter", "a-b", "-leading", "trailing-",
       "double--dash", "mid-the-of", "e-mail", "in-and-out"]
    # initials
    + ["J.R.R.", "U.S.A.", "J.K.", "A.B.C.", "H.G."]
    # digits
    + ["2nd", "3d", "42", "1990s", "10th", "007"]
)
WRAPS = ['"{}"', "({})", "{}:", "{}!", "{}?", "{};", "'{}'", "{},", "{}.", "[{}]"]
SEPS = [" "] * 90 + ["  ", "\t", " - ", " -- "]


def make_word():
    r = random.random()
    if r < 0.25:
        w = random.choice(SMALL)
    elif r < 0.55:
        w = random.choice(NORMAL)
    else:
        w = random.choice(TRICKY)
    if random.random() < 0.15:
        w = random.choice(WRAPS).format(w)
    return w


def make_title():
    n = random.randint(1, 10)
    parts = [make_word()]
    for _ in range(n - 1):
        parts.append(random.choice(SEPS))
        parts.append(make_word())
    t = "".join(parts)
    if random.random() < 0.15:
        t = t.upper()
    return t


def generate(count, forbidden):
    out, seen = [], set(forbidden)
    while len(out) < count:
        t = make_title()
        if t in seen or not t.strip() or t != t.strip():
            continue
        seen.add(t)
        out.append(t)
    return out


def write(name, lines):
    with open(os.path.join(HERE, "data", name), "w", encoding="utf-8", newline="\n") as f:
        for ln in lines:
            f.write(ln + "\n")


os.makedirs(os.path.join(HERE, "data"), exist_ok=True)
visible = generate(N, [])
hidden = generate(N, visible)

for inputs_name, expected_name, lines in [
    ("inputs.txt", "expected.txt", visible),
    ("hidden_inputs.txt", "hidden_expected.txt", hidden),
]:
    expected = []
    for ln in lines:
        out = titlecase(ln)  # the ORIGINAL code is the only source of answers
        assert "\n" not in out and "\r" not in out, repr(ln)
        expected.append(out)
    write(inputs_name, lines)
    write(expected_name, expected)
print("generated", len(visible), len(hidden))
