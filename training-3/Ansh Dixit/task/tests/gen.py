#!/usr/bin/env python3
"""Generate the visible and hidden data sets for the titlecase-go task.

Run from anywhere:  python3 tests/gen.py
Inputs are random (seeded) mixes of normal words and tricky cases. The expected
answers are NEVER written by hand: they come from running the ORIGINAL Python
titlecase() found in environment/python-titlecase, using its stdlib `re` code
path (the optional `regex` package is blocked on purpose).
"""
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent / "environment" / "python-titlecase"


def load_original():
    """Import the ORIGINAL Python titlecase (done lazily: Reward Kit imports every
    .py file in tests/, and the verifier image does not contain the Python repo)."""
    sys.modules["regex"] = None          # force the stdlib `re` fallback path
    sys.path.insert(0, str(REPO))
    from titlecase import titlecase, REGEX_AVAILABLE
    assert not REGEX_AVAILABLE, "the optional `regex` package must not be used"
    return titlecase


N = 2000
random.seed(1)
R = random

PUNCT = "!\"“#$%&'‘()*+,-–‒—―./:;?@[\\]_`{|}~"
EXTRA = "<>=^"                                    # characters outside PUNCT

SMALL = "a an and as at but by en for if in of on or the to v v. via vs vs. A An And The Of OR To".split()
NORMAL = ("lord rings war peace harry potter journey center earth gone wind quick brown fox jumps over lazy dog "
          "introduction chapter notes learning python guide modern history river cities night market story "
          "winter garden silent house long road final report summary data design theory practice").split()
ALLCAPS = "NASA FBI USA UNESCO BBC HTML CSS API SQL LORD RINGS WAR PEACE".split()
CAMEL = "iPhone eBay iOS macOS YouTube JavaScript PowerPoint gRPC pH mRNA".split()
CONSONANTS = "tv nyc brr tsk hmm mph cwm xyz rhythm st nth pm ft BRR Nyc".split()
MCS = "mcdonald McDonald MCDONALD macbeth mcgregor Mcq mcx MC mc McA mcAdams".split()
TITLES = "mr Mr MR mrs Mrs ms MS dr Dr DR mr. dr.".split()
APOS = ("o'neil O'Neil O'NEIL d'artagnan D'Artagnan l'amour L'Amour d‘artagnan o'brien's don't "
        "rock'n'roll it's o'clock l'ss d'x o'9 d'abc'x").split()
PERIOD = "example.com file.txt a.b v1.2 3.14 e.g. i.e. U.S. U.S.A. J.R.R. J.K. x.Y www.site.org/page etc.".split()
HYPHEN = ("self-aware up-to-date x-ray well-known a-b of-the foo-of to-do state-of-the-art "
          "mother-in-law -leading trailing- a--b two-and-a-half e-mail").split()
SLASH = "and/or he/she w/o http://x.com/a a//b TCP/IP read/write input/output /usr/bin a/ /b".split()
DIGITS = "1st 2nd 3d 10k 2024 3x 007 4-h 1/2 24/7".split()
UNDER = "_foo __init__ snake_case _x_ a_b _".split()
WRAPPED = ["“quoted”", "‘single’", "(paren)", "[bracket]", "\"hello\"", "'world'", "{brace}", "~tilde~",
           "*star*", "#tag", "@user", "$money", "100%", "&and", "«x»", "<angle>", "=eq", "^caret"]
TRAIL_SMALL = "of. to! v. vs. the? a, in; and: or) by\" at' for- as."  .split()
SEPS = [" "] * 12 + ["  ", "\t", " \t "]
SUBSEPS = [": ", ". ", "; ", "? ", "! ", "- ", "– ", "— ", "‒ ", "― "]

POOLS = [SMALL, NORMAL, NORMAL, NORMAL, ALLCAPS, CAMEL, CONSONANTS, MCS, TITLES, APOS, PERIOD, HYPHEN,
         SLASH, DIGITS, UNDER, WRAPPED, TRAIL_SMALL]


def junk_word():
    alpha = "abcxyzABCXYZaeiotvsdlmcrn0129" + PUNCT + EXTRA
    return "".join(random.choice(alpha) for _ in range(random.randint(1, 7)))


def one_word():
    k = random.random()
    if k < 0.18:
        w = junk_word()
    else:
        w = random.choice(random.choice(POOLS))
    if random.random() < 0.12:
        w = random.choice(PUNCT) + w
    if random.random() < 0.12:
        w = w + random.choice(PUNCT)
    if random.random() < 0.08:
        w = w.upper()
    elif random.random() < 0.08:
        w = w.lower()
    return w


def make_line():
    n = random.randint(1, 10)
    s = ""
    for i in range(n):
        s += one_word()
        if i < n - 1:
            s += random.choice(SUBSEPS) if random.random() < 0.15 else random.choice(SEPS)
    if random.random() < 0.06:
        s = " " + s
    if random.random() < 0.06:
        s = s + " "
    r = random.random()
    if r < 0.15:
        s = s.upper()
    elif r < 0.30:
        s = s.lower()
    return s


def build(seen):
    out = []
    while len(out) < N:
        s = make_line()
        if s.strip() == "" or s in seen:
            continue
        seen.add(s)
        out.append(s)
    return out


def write(name, lines):
    (HERE / "data" / name).write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main():
    titlecase = load_original()
    (HERE / "data").mkdir(exist_ok=True)
    seen = set()
    visible = build(seen)
    hidden = build(seen)
    for inp, exp, ins, exps in (("inputs.txt", "expected.txt", visible, None),
                                ("hidden_inputs.txt", "hidden_expected.txt", hidden, None)):
        write(inp, ins)
        answers = [titlecase(x) for x in ins]
        assert all("\n" not in a and "\r" not in a for a in answers)
        assert len(answers) == len(ins)
        write(exp, answers)
    print("wrote", N, "visible +", N, "hidden lines to", HERE / "data")


if __name__ == "__main__":
    main()
