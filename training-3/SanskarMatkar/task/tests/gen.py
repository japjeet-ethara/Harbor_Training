#!/usr/bin/env python3
"""Generate the visible and hidden input sets and freeze the expected answers.

Run from anywhere:  python3 tests/gen.py
Needs the original repo checked out next to the task folder:  ../python-titlecase

The expected answers are NEVER written by hand: every line in expected.txt and
hidden_expected.txt is the output of the ORIGINAL Python titlecase() run on the
matching input line. The optional `regex` package is blocked so the reference
is the default, standard-library-`re` behaviour.
"""
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent            # .../titlecase-go/tests
REPO = HERE.parent.parent / "python-titlecase"    # sibling of the task folder
DATA = HERE / "data"

sys.modules["regex"] = None  # force the stdlib `re` fallback in titlecase
sys.path.insert(0, str(REPO))
import titlecase as _tc  # noqa: E402

assert _tc.REGEX_AVAILABLE is False, "reference must use stdlib re"
assert _tc.__version__ == "2.4.1", _tc.__version__
titlecase = _tc.titlecase

# ---------------------------------------------------------------- vocabulary
COMMON = """
lord rings tale two cities guide end world story season service fact place day
night river house garden dream light shadow time love war peace king queen city
road home water fire stone heart mind book song game code data system network
report history future market power money island ocean mountain forest winter
summer spring autumn letter secret journey return rise fall art science music
apple orange table window door street bridge castle machine engine voice
""".split()
SMALL = "a an and as at but by en for if in of on or the to v v. via vs vs.".split()
NEAR_SMALL = "ant another anda ask ate butter byte end form ifs into off one ore "\
    "then tone van vial versus thee too tot aa".split()
MIXED = "iPhone iPad eBay macOS JavaScript iOS YouTube PowerPoint McKinsey "\
    "LaTeX GitHub OpenAI xAI pH mRNA DeLorean".split()
INLINE = "example.com e.g. i.e. U.S. a.b.c node.js v1.2 www.site.org a.a "\
    "the.end v.x Ph.D. etc. 3.14 file.TXT".split()
APOS = ["o'neil", "d'artagnan", "l'oreal", "O'BRIEN", "o'neil's", "d'angelo''",
        "don't", "it's", "rock'n'roll", "’tis", "‘tis", "o‘neil",
        "l'eau", "D'ARCY", "o'", "d'a", "l'x's", "o'reilly'", "can't", "y'all",
        "'tis", "o'clock", "D'Souza"]
MAC = ["mcdonald", "mcfly", "MCDONALD", "mcd", "mc", "Mcx", "mcdonald's",
       "MCDONALD'S", "mcthe", "mcA", "Mcintosh", "mCdonald", "MCX1", "mc_do",
       "mcthe-end", "MacDonald", "macbeth", "mc-hammer"]
TITLES = ["mr", "mrs", "ms", "dr", "MR", "Dr", "DR", "mrs.", "dr.", "Ms", "mRs"]
SLASH = ["either/or", "and/or", "http://x.com/a", "a/b/c", "/usr/bin", "TCP/IP",
         "foo/the/bar", "the/end", "in/out", "1/2", "the//end", "on/off-line",
         "/the", "the/"]
HYPHEN = ["well-known", "on-demand", "e-mail", "x-ray", "re-enter", "-foo",
          "foo-", "step-by-step", "the-end", "end-to", "well-KNOWN", "TWO-WAY",
          "mid-1990s", "a-b", "co-op", "--", "one--two", "self-iPhone",
          "nyc-based", "the-iPhone", "x-v.", "vs.-them"]
CONSONANT = ["cnn", "bbc", "nbc", "st", "xyz", "rhythm", "html", "sql", "nyc",
             "pdf", "tv", "BBC", "Cnn", "crwth", "sh", "psst", "hmm", "brrr"]
NUMBERS = ["1st", "2nd", "1984", "3d", "42", "100%", "#1", "$5", "7th", "24/7",
           "3-d", "2010s"]
UNDERSCORE = ["_foo", "foo_bar", "__init__", "_the", "the_", "_"]
ACCENT = ["café", "élan", "über", "niño", "ÉCOLE",
          "façade", "résumé", "naïve", "à", "À",
          "öl", "été", "Ångström", "des", "au", "ça",
          "índice", "ópera", "émile-zola"]
PUNCT_WORDS = ['"the"', "(a)", "[in]", "“quote”", "‘single’",
               "'tis", "...", "--the", "!!", "(the", "of)", "“the”",
               "the?", "the?!", "in.", "vs..", "*bold*", "#tag", "@user",
               "—the", "–a", "~", "(", ")", "{or}", "<a>", "the,",
               "end;", "of:", "a!", "to.", "v.!", "v.."]
SUBPHRASE_P = [":", ".", ";", "?", "!", "-", "–", "‒", "—",
               "―", ",", "…"]
ALLCAPS_INITIALS = ["U.S.", "A.B.C.", "I.B.M.", "U.S.A.", "A.", "A.B", "N.Y.C.",
                    "A.BC", "U.S"]
SPACES = [" "] * 30 + ["  ", "\t", " ", " ", "   ", " \t"]

POOLS = [
    (COMMON, 30), (SMALL, 22), (NEAR_SMALL, 4), (MIXED, 4), (INLINE, 4),
    (APOS, 4), (MAC, 4), (TITLES, 3), (SLASH, 3), (HYPHEN, 4), (CONSONANT, 4),
    (NUMBERS, 3), (UNDERSCORE, 1), (ACCENT, 4), (PUNCT_WORDS, 5),
]
POOL_LISTS = [p for p, _ in POOLS]
POOL_WEIGHTS = [w for _, w in POOLS]


def recase(rng, word):
    r = rng.random()
    if r < 0.70:
        return word
    if r < 0.82:
        return word.upper()
    if r < 0.92:
        return word[:1].upper() + word[1:]
    return word.lower()


def pick_word(rng):
    pool = rng.choices(POOL_LISTS, POOL_WEIGHTS)[0]
    return recase(rng, rng.choice(pool))


def make_title(rng):
    style = rng.random()
    n = rng.randint(1, 9)
    words = [pick_word(rng) for _ in range(n)]

    # sub-phrase punctuation glued to a word, followed by a small word
    if n >= 2 and rng.random() < 0.35:
        i = rng.randrange(n - 1)
        p = rng.choice(SUBPHRASE_P)
        if p in "-–‒—―" and rng.random() < 0.5:
            words.insert(i + 1, p)          # free-standing dash: "foo - the"
            j = i + 2
        else:
            words[i] = words[i] + p         # glued: "foo: the"
            j = i + 1
        if j < len(words) and rng.random() < 0.7:
            words[j] = rng.choice(SMALL + NEAR_SMALL)

    if style < 0.10:  # all-caps line, sometimes with initials
        if rng.random() < 0.6:
            words.insert(rng.randrange(len(words) + 1), rng.choice(ALLCAPS_INITIALS))
        words = [w.upper() for w in words]

    out = words[0]
    for w in words[1:]:
        out += rng.choice(SPACES) + w

    r = rng.random()
    if r < 0.04:
        out = " " + out
    elif r < 0.08:
        out = out + " "
    elif r < 0.09:
        out = "\t" + out + " "
    elif r < 0.095:
        out = ""                      # empty line
    elif r < 0.10:
        out = rng.choice(["   ", "\t", " "])  # whitespace-only line
    return out


def build(rng, count, avoid):
    lines, seen = [], set(avoid)
    while len(lines) < count:
        t = make_title(rng)
        if t in seen and t.strip():
            continue
        seen.add(t)
        assert "\n" not in t and "\r" not in t
        lines.append(t)
    return lines


def freeze(lines):
    out = []
    for line in lines:
        res = titlecase(line)
        assert "\n" not in res and "\r" not in res, repr(line)
        out.append(res)
    return out


def write(path, lines):
    path.write_text("".join(l + "\n" for l in lines), encoding="utf-8")


def main():
    rng = random.Random(1)
    random.seed(1)
    DATA.mkdir(parents=True, exist_ok=True)
    visible = build(rng, 2000, ())
    hidden = build(rng, 2000, visible)
    assert not (set(visible) & set(hidden)) - {""} - {"   ", "\t", " "}
    write(DATA / "inputs.txt", visible)
    write(DATA / "expected.txt", freeze(visible))
    write(DATA / "hidden_inputs.txt", hidden)
    write(DATA / "hidden_expected.txt", freeze(hidden))
    print("wrote", *(p.name for p in sorted(DATA.iterdir())))


if __name__ == "__main__":
    main()
