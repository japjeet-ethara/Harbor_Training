#!/usr/bin/env python3
"""Generate the test data for the titlecase-go task.

Inputs are made with a fixed random seed (always the same output).
Expected answers are NEVER written by hand: they are produced by running the
ORIGINAL Python titlecase() from the python-titlecase checkout.

Outputs (in tests/data/):
    inputs.txt            2000 visible-set titles
    expected.txt          answers for inputs.txt
    hidden_inputs.txt     a different 2000 titles (used for grading)
    hidden_expected.txt   answers for hidden_inputs.txt

Usage:
    python tests/gen.py                      # uses ../python-titlecase next to this task
    TITLECASE_REPO=/path/to/repo python tests/gen.py
Needs the optional `regex` package (pip install regex) so the reference runs in
its Unicode mode (REGEX_AVAILABLE = True).
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
N = 2000

# NOTE: this file lives in tests/, and Reward Kit imports every tests/*.py file.
# So importing it must have NO side effects: everything that needs the Python
# reference runs inside main().


def load_reference():
    """Import the ORIGINAL python-titlecase (needs the optional `regex` package)."""
    repo = os.environ.get(
        "TITLECASE_REPO",
        os.path.normpath(os.path.join(HERE, "..", "..", "python-titlecase")),
    )
    if not os.path.isdir(os.path.join(repo, "titlecase")):
        # fallback: the copy shipped inside the task's Docker build context
        repo = os.path.normpath(os.path.join(HERE, "..", "environment", "python-titlecase"))
    sys.path.insert(0, repo)
    import titlecase  # noqa: E402

    if not titlecase.REGEX_AVAILABLE:
        sys.exit("The `regex` package is required (pip install regex): "
                 "the reference must run in Unicode mode.")
    return titlecase


# --------------------------------------------------------------------------
# Vocabulary
# --------------------------------------------------------------------------
NORMAL = """
lord rings tale cities story night river garden window summer winter market
journey mountain ocean engine library history science music paper silver golden
quiet bridge island forest shadow thunder letter morning evening machine memory
culture design network system program project report review guide manual notes
rhythm gym crypt myth lynx sky fly dry try hymn syrup nymph
question answer problem solution method result trend change growth future past
brave little great small long short fast slow deep high low open closed first last
word title phrase sentence chapter section volume edition series season episode
hmm tsk brr pst shh nth cwm psst grr
""".split()

SMALL = "a an and as at but by en for if in of on or the to v v. via vs vs.".split()

NAMES_MC = ["mcdonald", "McDonald", "MCDONALD", "mcallister", "mcintosh", "McCoy",
            "mccartney", "MCCARTNEY", "mcc", "mc2", "mcx", "Mcdonald's", "macarthur",
            "MacArthur", "macdonald", "MAC", "mcmillan", "mCdonald"]
HONOR = ["dr", "Dr", "DR", "dR", "mr", "Mr", "MR", "mrs", "Mrs", "MRS", "ms", "Ms", "MS",
         "mr.", "dr.", "mrs.", "ms.", "mx", "drs", "mss"]
APOS = ["o'neil", "O'Neil", "d'artagnan", "D'Artagnan", "l'amour", "L'Amour", "o'brien",
        "o'reilly's", "d'angelo", "l'ours", "o‘neil", "d‘artagnan", "l‘été", "o'neil's",
        "d'a", "o'", "d'", "x'ab", "don't", "it's", "rock'n'roll", "o'neil''", "l'amour'S",
        "d'artagnan's", "O'NEIL", "D'ARTAGNAN"]
INLINE = ["example.com", "u.s.a.", "e.g.", "i.e.", "a.m.", "p.m.", "www.site.org", "node.js",
          "v1.2.3", "file.txt", "a.b", "A.b", "x.Y", "web.mit.edu", "ph.d", "Ph.D.", "U.S.",
          "st.", "no.", "vs.", "v.", "etc.", "3.14", "a.1", "1.a", "(a.b)", "'e.g.'"]
MIXED = ["iPhone", "eBay", "iOS", "YouTube", "macOS", "PostgreSQL", "JavaScript", "LaTeX",
         "nVidia", "McAfee", "inDesign", "iN", "aS", "oR", "tHe", "bY", "iF", "ePub", "ipAd",
         "(iPhone)", "'eBay'", "-iOS", "\"YouTube\"", "xX", "aB", "A-b", "mRNA", "pH",
         "ÉCOLE", "éCOLE", "naÏve", "überCool", "ÀB"]
ACRO = ["NASA", "FBI", "UK", "USA", "HTML", "GPU", "CPU", "NATO", "UN", "ID", "TV", "OK",
        "IBM", "BBC", "PDF", "SQL", "AI", "ML", "I", "A", "AN", "OF", "THE", "IN"]
INITIALS = ["J.R.R.", "A.B.", "A.B.C.", "J.K.", "U.S.A.", "U.K.", "A.", "A.B", "A.BC", "A..B",
            "J.R.R", "E.T.", "U.S", "a.b.c.", "J.r.R.", "X.Y.Z"]
HYPHEN = ["state-of-the-art", "well-known", "e-mail", "x-ray", "-leading", "trailing-", "a--b",
          "double--hyphen", "-", "--", "---", "of-the", "in-and-out", "t-shirt", "co-op",
          "mother-in-law", "pre-war", "ex-wife", "state-of-the-ART", "iPhone-case", "the-end",
          "a-", "-a", "1990-2000", "mc-donald", "o'neil-smith", "dr-who", "nasa-funded",
          "up-to-date", "b-c-d", "re-enter", "long-term", "high-end-for"]
SLASH = ["and/or", "either/or", "w/o", "http://x.com//path", "a/b/c", "/usr/bin", "trailing/",
         "//", "a//b", "r/w", "24/7", "his/her", "input/output", "of/in", "/", "the/the",
         "AC/DC", "a/", "/a", "s/he", "c/o", "n/a", "km/h", "and/or/of", "x/y-z", "a-b/c-d"]
PUNCT_WRAP = ["(the)", "\"quoted\"", "'single'", "“curly”", "‘curly’", "[of]", "{in}", "(a)",
              "word:", "word;", "what?", "wow!", "end.", "a,", "of,", "to.", "in!", "by?", "or:",
              "(and)", "\"a", "a\"", "'of", "of'", "“the", "the”", "…", "—", "–", "-", "&",
              "$100", "100%", "#hashtag", "@user", "~tilde", "*star*", "_under_", "`tick`",
              "(", ")", "((a))", "[[in]]", "{{the}}", "!?", ".", "..", ":)", "a.", "of.", "or;"]
UNI = ["à", "la", "carte", "éclair", "über", "naïve", "café", "ñandú", "résumé", "œuvre",
       "ça", "øl", "åre", "ÉCOLE", "ÉCLAIR", "ÜBER", "À", "É", "Ñ", "çà", "ébène", "ôtre",
       "mañana", "señor", "crème", "brûlée", "façade", "jalapeño", "piñata", "coöperate",
       "(éclair)", "“über”", "é-é", "ü/ö", "ø.ø", "Ø", "æon", "Æon", "ÆON", "i", "í", "ï"]
NUMS = ["42", "3rd", "2nd-hand", "1.5", "100%", "1st", "007", "2000s", "5k", "10x", "3d",
        "1/2", "9-5", "24x7", "v2", "v2.0", "b2b", "p2p", "4chan", "x86", "x86-64", "a1", "1a"]
SEPS_PUNCT = [": ", "; ", ". ", "? ", "! ", " - ", " – ", " — ", " ‒ ", " ― ", "- ", "– ", "— ",
              "-  ", ":  ", ".  ", ": - ", "... "]
SPACES = [" "] * 30 + ["  ", "   ", "\t", " \t", "\u00a0", "\u2003", "\u3000", "\u202f"]

# --------------------------------------------------------------------------
# Building blocks
# --------------------------------------------------------------------------
POOLS = [
    (NORMAL, 38), (SMALL, 20), (NAMES_MC, 3), (HONOR, 3), (APOS, 4), (INLINE, 4), (MIXED, 4),
    (ACRO, 4), (INITIALS, 2), (HYPHEN, 6), (SLASH, 4), (PUNCT_WRAP, 4), (UNI, 6), (NUMS, 3),
]
_WEIGHTED = [pool for pool, w in POOLS for _ in range(w)]


def recase(rng, w):
    r = rng.random()
    if r < 0.60:
        return w
    if r < 0.75:
        return w.upper()
    if r < 0.88:
        return w.capitalize() if w else w
    if r < 0.94:
        return w.lower()
    # random per-letter case
    return "".join(c.upper() if rng.random() < 0.4 else c.lower() for c in w)


def word(rng):
    pool = rng.choice(_WEIGHTED)
    w = rng.choice(pool)
    if pool is NORMAL or pool is SMALL or pool is UNI:
        w = recase(rng, w)
    elif rng.random() < 0.15:
        w = recase(rng, w)
    return w


def join(rng, words):
    out = []
    for i, w in enumerate(words):
        if i:
            r = rng.random()
            if r < 0.10:
                out.append(rng.choice(SEPS_PUNCT))
            else:
                out.append(rng.choice(SPACES))
        out.append(w)
    return "".join(out)


def natural(rng):
    n = rng.choice([1, 2, 3, 3, 4, 4, 5, 5, 6, 7, 8, 9, 11, 14])
    return join(rng, [word(rng) for _ in range(n)])


def allcaps_line(rng):
    return natural(rng).upper()


def small_edges(rng):
    """Small words at the start / end of a line, with trailing punctuation."""
    n = rng.choice([1, 2, 3, 4, 5])
    mid = [word(rng) for _ in range(n)]
    first = [recase(rng, rng.choice(SMALL))] if rng.random() < 0.6 else []
    last = [recase(rng, rng.choice(SMALL)) + rng.choice(["", "", ".", "!", "?", ":", ";", ",", "'", "\"", ")", "..", "-"])] if rng.random() < 0.7 else []
    lead = rng.choice(["", "", "", "(", "\"", "'", "“", "‘", "[", "...", "- "])
    return lead + join(rng, first + mid + last)


def subphrase(rng):
    parts = []
    for _ in range(rng.choice([2, 2, 3, 4])):
        n = rng.choice([1, 2, 3])
        s = join(rng, [word(rng) for _ in range(n)])
        parts.append(s)
    out = parts[0]
    for p in parts[1:]:
        sep = rng.choice(SEPS_PUNCT)
        if rng.random() < 0.7:
            p = rng.choice(SMALL).lower() + (" " + p if rng.random() < 0.7 else p)
        out += sep + p
    return out


def punct_edges(rng):
    w = [word(rng) for _ in range(rng.choice([1, 2, 3, 4]))]
    s = join(rng, w)
    return rng.choice(["", "(", "\"", "'", "“", "‘", "[", "{", "...", "¿", "¡"]) + s + rng.choice(["", ".", "!", "?", ")", "\"", "'", "”", "’", "…", "]", ":", ";"])


def whitespace_edges(rng):
    s = natural(rng)
    return rng.choice(["", " ", "  ", "\t", "\u00a0"]) + s + rng.choice(["", " ", "  ", "\t", "\u2003"])


def hard_mix(rng):
    """Dense line made only of the tricky pools."""
    pools = [NAMES_MC, HONOR, APOS, INLINE, MIXED, ACRO, INITIALS, HYPHEN, SLASH, PUNCT_WRAP, UNI, NUMS, SMALL]
    n = rng.choice([2, 3, 4, 5, 6])
    ws = [rng.choice(rng.choice(pools)) for _ in range(n)]
    ws = [recase(rng, w) if rng.random() < 0.3 else w for w in ws]
    return join(rng, ws)


def single(rng):
    return word(rng)


def weird(rng):
    return rng.choice([
        "", " ", "  ", "\t", "-", "--", "/", "//", ".", "..", "...", ":", "a", "A", "I", "v.", "vs.",
        "the", "THE", "The", "of", "OF", "in.", "a:", " a ", "\ta", "'a", "'", "''", "\"", "a/", "/a",
        "a-", "-a", "mc", "Mc", "MC", "mcd", "mcdo", "MCD", "o'", "o'n", "dr", "Dr.", "x.y", "X.Y.",
        "A.", "A.B.", "A.B.C", "bcd", "BCD", "bc", "BC", "bcdy", "st", "St", "NASA", "nasa", "iPhone",
        "à", "É", "é.é", "é-é", "(a)", "(A)", "[v.]", "{vs.}", "a b", "a  b", "a\tb", "a\u00a0b",
        ". a", ": a", "; an", "? and", "! as", "- at", "– but", "— by", "‒ en", "― for",
        "x: a", "x. an", "x; and", "x? as", "x! at", "x- but", "x– by", "x— en", "x‒ for", "x― if",
        "x: in", "x: of", "x: on", "x: or", "x: the", "x: to", "x: v", "x: v.", "x: via", "x: vs", "x: vs.",
        "x: android", "x: inDesign", "x: antelope", "x: orange", "x: toast", "x: theory", "x: vsx",
        "x:  a", "x :a", "x:a",
    ])


GENERATORS = [
    (natural, 34), (allcaps_line, 6), (small_edges, 14), (subphrase, 10), (punct_edges, 8),
    (whitespace_edges, 5), (hard_mix, 14), (single, 5), (weird, 4),
]
_GEN = [g for g, w in GENERATORS for _ in range(w)]


def make_set(rng, n, forbid):
    seen = set(forbid)
    out = []
    while len(out) < n:
        s = rng.choice(_GEN)(rng)
        if "\n" in s or "\r" in s:
            continue
        if s in seen:
            continue
        seen.add(s)
        out.append(s)
    return out


def write_lines(path, lines):
    # newline-terminated, '\n' only, UTF-8
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for ln in lines:
            f.write(ln + "\n")


def main():
    _tc = load_reference()
    random.seed(1)   # always the same output
    rng = random     # all helpers call rng.choice / rng.random
    visible = make_set(rng, N, forbid=())
    hidden = make_set(rng, N, forbid=visible)  # a DIFFERENT 2000 titles
    assert not set(visible) & set(hidden)

    os.makedirs(DATA, exist_ok=True)
    for name, titles in (("", visible), ("hidden_", hidden)):
        write_lines(os.path.join(DATA, name + "inputs.txt"), titles)
        # The truth comes from the ORIGINAL implementation, one call per line.
        answers = [_tc.titlecase(t) for t in titles]
        for t, a in zip(titles, answers):
            assert "\n" not in a and "\r" not in a, (t, a)
        write_lines(os.path.join(DATA, name + "expected.txt"), answers)
    print("wrote", DATA)


if __name__ == "__main__":
    main()
