#!/usr/bin/env python3
"""Generate the visible and hidden test sets for the titlecase-go task.

Run by the task author (NOT at grading time):

    python tests/gen.py

Needs the optional `regex` package (the original prefers it):  pip install regex

The expected answers always come from running the ORIGINAL Python titlecase()
(../python-titlecase, same commit that is copied into the task image). They are
never written by hand.

Output (tests/data/):
    inputs.txt            2000 visible titles
    expected.txt          original titlecase() of each visible title
    hidden_inputs.txt     a different 2000 titles (used for grading)
    hidden_expected.txt   original titlecase() of each hidden title

Note: Reward Kit imports every .py file in tests/. Everything here therefore lives
behind `if __name__ == "__main__"`, so importing this file does nothing.
"""
import random
import sys
from pathlib import Path

sys.dont_write_bytecode = True   # never leave __pycache__ inside the source repo

N = 2000
HERE = Path(__file__).resolve().parent                 # tests/
DATA = HERE / "data"

# --------------------------------------------------------------------------
# Word pools
# --------------------------------------------------------------------------
COMMON = """lord rings tale cities game thrones war peace pride prejudice great
expectations silent night river road mountain garden house city world story
secret history future journey dream shadow light storm summer winter spring
autumn captain ocean island forest desert kingdom empire machine learning
python programming guide complete handbook introduction advanced beginners
quick brown fox jumps over lazy dog hello goodbye morning evening yesterday
tomorrow forever never always sometimes everything nothing someone anything
chronicles adventures mystery voyage legend rise fall return revenge begins
ends awakening requiem harvest silence thunder whisper bridge tower castle
engineering database network protocol design pattern review notes report
analysis results study methods approach framework system theory practice""".split()

SMALL = ["a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in",
         "of", "on", "or", "the", "to", "v", "v.", "via", "vs", "vs."]

ACRONYMS = ["NASA", "FBI", "USA", "IBM", "HTTP", "HTML", "CPU", "GPU", "NATO",
            "UNESCO", "DNA", "AI", "ML", "SQL", "API", "CEO", "UK", "EU", "UN"]

CONSONANT_ONLY = ["tv", "nyc", "ltd", "bcd", "st", "mph", "nth", "xyz", "pdf",
                  "cd", "dvd", "rpm", "hmm", "shh", "brr", "tsk", "cwm", "crwth",
                  "Ltd", "PhD", "phd", "grrr", "Mgr", "kbps"]

MIXED_CASE = ["iPhone", "eBay", "macOS", "YouTube", "DiCaprio", "McDonald",
              "iOS", "PowerPoint", "JavaScript", "GitHub", "LaTeX", "bitTorrent",
              "O'Neil", "D'Artagnan", "MacBook", "WiFi", "PlayStation", "xBox",
              "mRNA", "pH", "kHz", "dB", "eBooks", "iPad"]

MC = ["mcdonald", "mcgregor", "MCDONALD", "McDonald", "mcd", "mcx", "mc", "mcdonalds",
      "MCGREGOR", "mcintosh", "mccartney", "McCartney", "mcdonald-smith",
      "mc1", "mcA", "MC", "Mc", "mcm", "mcfly", "MacDonald", "macdonald"]

HONORIFICS = ["mr", "mrs", "ms", "dr", "Mr", "Mrs", "Ms", "Dr", "MR", "MRS",
              "DR", "dR", "mr.", "dr.", "Dr.", "mrs.", "ms.", "Mr.", "mister"]

APOS = ["o'neil", "d'artagnan", "l'amour", "o'brien", "d'angelo", "l'oreal",
        "O'NEIL", "D'ARTAGNAN", "L'AMOUR", "o'neil's", "d'artagnan's",
        "o‘brien", "d‘angelo", "don't", "it's", "rock'n'roll", "dogs'",
        "'tis", "'em", "o'connor", "l'", "d'", "o'", "o'x", "d'a's", "l'am''",
        "o'neills", "o'neil''", "D'Arcy", "d'ARCY", "john's", "ma'am",
        "o'k", "d'ss", "l'ss"]

URLS = ["http://example.com", "https://example.com/foo", "www.example.com",
        "user@example.com", "example.com/foo-bar", "http://x.org//y",
        "e.g.", "i.e.", "etc.", "u.s.", "U.S.A.", "U.S.", "J.R.R.", "A.B.",
        "J.K.", "a.b.c", "node.js", "file.txt", "v1.2.3", "3.14", "a.B", "x.Y.z",
        "S.W.A.T.", "A.B.C", "M.C.", "J.R.R", "U.S", "a.", "A."]

HYPHEN = ["state-of-the-art", "well-known", "x-ray", "-leading", "trailing-",
          "double--dash", "3-d", "e-mail", "the-end", "of-the", "up-to-date",
          "mother-in-law", "A-Team", "t-shirt", "pre-1900", "self-made",
          "non-OCR", "to-do", "once-in-a-lifetime", "a-b-c", "x-", "-x", "-",
          "--", "in-between", "by-product", "cross-site", "IBM-compatible",
          "UK-based", "the-a-of", "v-day", "high-end/low-end", "ex-wife",
          "STATE-OF-THE-ART", "WELL-KNOWN", "Spider-Man", "e-commerce"]

SLASH = ["and/or", "either/or", "w/o", "24/7", "a//b", "http://x//y", "n/a",
         "yes/no", "input/output", "TCP/IP", "AC/DC", "his/her", "a/b/c",
         "/leading", "trailing/", "the/of", "by/for", "/", "//", "the/end",
         "s/he", "on/off", "client/server", "I/O", "and/or/the"]

DIGITS = ["1st", "2nd", "3rd", "4k", "3d", "2024", "10%", "$5", "#1", "a1b",
          "1a", "007", "9to5", "42", "3.5", "100%", "1,000", "#hashtag",
          "5th", "r2d2", "c3po", "f1", "4x4", "1984", "24", "a1", "of2", "x2y"]

WRAPPED_FMT = ['({})', '"{}"', "'{}'", "[{}]", "{{{}}}", "“{}”",
               "‘{}’", "{},", "{}.", "{}!", "{}?", "{}:", "{};",
               "{}...", "—{}", "{}—", "-{}", "{}-", "*{}*", "_{}_",
               "<{}>", "`{}`", "–{}", "#{}", "@{}", "~{}~", "...{}",
               "({}).", "\"{}\"!", "'{}',", "“{}", "{}”"]

UNICODE_WORDS = ["café", "naïve", "über", "ñandú", "École", "ÉCOLE", "señor",
                 "à", "la", "carte", "Ångström", "ÅNGSTRÖM", "façade", "jalapeño",
                 "crème", "brûlée", "smörgåsbord", "çok", "über-cool", "Zoë",
                 "ÀÉÎ", "élan", "ærø", "øl", "naïve-ish", "école/uni",
                 "ÑANDÚ", "žluťoučký", "łódź", "istanbul"]

WEIRD = ["...", "?!", "--", "-", "***", "123", "a", "v", "v.", "vs.", "&",
         "+", "=", "~", "|", "\\", "x\\y", "^", "<>", "%", "!!!", "(", ")",
         "'", '"', "—", "–", "‘", "“", "_", "__", "_x_",
         "snake_case_word", "of_x", "a_b", "x_of", "foo__bar", "(a)", "(of)"]

SEPARATORS_RARE = ["  ", "\t", " ", "   ", "  ", " ", "　", "\t\t"]
JOINERS = [": ", ". ", "? ", "! ", "; ", "- ", " – ", " — ", "— ",
           "– ", "― ", "‒ "]


def pick_word(rng):
    """One token. Weighted towards realistic words, with many tricky ones."""
    r = rng.random()
    if r < 0.30:
        return rng.choice(COMMON)
    if r < 0.45:
        return rng.choice(SMALL)
    if r < 0.50:
        return rng.choice(ACRONYMS)
    if r < 0.54:
        return rng.choice(CONSONANT_ONLY)
    if r < 0.58:
        return rng.choice(MIXED_CASE)
    if r < 0.62:
        return rng.choice(MC)
    if r < 0.65:
        return rng.choice(HONORIFICS)
    if r < 0.69:
        return rng.choice(APOS)
    if r < 0.73:
        return rng.choice(URLS)
    if r < 0.78:
        return rng.choice(HYPHEN)
    if r < 0.82:
        return rng.choice(SLASH)
    if r < 0.85:
        return rng.choice(DIGITS)
    if r < 0.92:
        base = rng.choice(COMMON + SMALL + ACRONYMS + ["O'Neil", "x", "mcdonald"])
        return rng.choice(WRAPPED_FMT).format(base)
    if r < 0.96:
        return rng.choice(UNICODE_WORDS)
    return rng.choice(WEIRD)


def case_variant(rng, w):
    """Randomly re-case a token (lower / UPPER / Capitalized / swapped)."""
    r = rng.random()
    if r < 0.60:
        return w
    if r < 0.75:
        return w.lower()
    if r < 0.85:
        return w.upper()
    if r < 0.93:
        return w[:1].upper() + w[1:]
    return w.swapcase()


def make_title(rng):
    n = rng.choice([1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 7, 8, 9, 11, 14])
    words = []
    for _ in range(n):
        w = pick_word(rng)
        words.append(case_variant(rng, w))
    # Mostly one space, sometimes unusual whitespace.
    parts = []
    for i, w in enumerate(words):
        parts.append(w)
        if i < len(words) - 1:
            r = rng.random()
            if r < 0.04:
                parts.append(rng.choice(SEPARATORS_RARE))
            elif r < 0.10 and w[-1:] not in ":.;?!":
                # glue a joiner so SUBPHRASE (": the") rules are exercised
                parts.append(rng.choice(JOINERS))
            else:
                parts.append(" ")
    title = "".join(parts)

    r = rng.random()
    if r < 0.10:
        title = title.upper()                    # all-caps line
    elif r < 0.45:
        title = title.lower()                    # all-lowercase line
    elif r < 0.50:
        title = title.swapcase()
    # rare: leading / trailing whitespace
    r = rng.random()
    if r < 0.02:
        title = " " + title
    elif r < 0.04:
        title = title + " "
    elif r < 0.05:
        title = "\t" + title
    # rare: a second clause after a joiner
    if rng.random() < 0.12:
        title = title + rng.choice(JOINERS) + case_variant(
            rng, " ".join(pick_word(rng) for _ in range(rng.choice([1, 2, 3]))))
    return title


def fixed_lines():
    """A few deliberately nasty single-line cases, always present."""
    return [
        "  ", " ", "the", "THE", "a", "of", "v.", "vs.", "x v. y", "x vs. y",
        "the lord of the rings", "THE LORD OF THE RINGS", "J.R.R. TOLKIEN",
        "mcdonald and macdonald", "o'neil d'artagnan l'amour",
        "state-of-the-art design", "what is it for?", "look at!", "something to",
        "Chapter 1: the end", "hello. a world", "wow - an idea", "a: b",
        "and/or either/or", "see http://example.com/foo now", "NASA's new rocket",
        "iPhone and eBay", "ab cd bcd stop", " the cat ",
    ]


def generate(rng):
    seen = set()
    out = []
    for line in fixed_lines():
        if line not in seen:
            seen.add(line)
            out.append(line)
    while len(out) < 2 * N:
        t = make_title(rng)
        if not t or "\n" in t or "\r" in t or t in seen:
            continue
        seen.add(t)
        out.append(t)
    return out


def main():
    repo = HERE.parents[1] / "python-titlecase"            # ../python-titlecase
    sys.path.insert(0, str(repo))
    from titlecase import titlecase, REGEX_AVAILABLE
    if not REGEX_AVAILABLE:
        sys.exit("The `regex` package is required (pip install regex): "
                 "the expected answers must come from the regex code path.")

    rng = random.Random(1)
    random.seed(1)                                   # as required by the brief
    lines = generate(rng)
    # The nasty fixed lines go to the visible set; shuffle the rest deterministically.
    fixed = lines[:len(fixed_lines())]
    rest = lines[len(fixed):]
    rng.shuffle(rest)
    visible = (fixed + rest)[:N]
    hidden = rest[N - len(fixed):][:N]
    assert len(visible) == N and len(hidden) == N
    assert not set(visible) & set(hidden)

    DATA.mkdir(exist_ok=True)

    def write(name, items):
        # newline="\n" so Windows does not rewrite line endings
        with open(DATA / name, "w", encoding="utf-8", newline="\n") as f:
            for item in items:
                f.write(item + "\n")

    write("inputs.txt", visible)
    write("expected.txt", [titlecase(x) for x in visible])
    write("hidden_inputs.txt", hidden)
    write("hidden_expected.txt", [titlecase(x) for x in hidden])
    print(f"wrote {N} visible + {N} hidden titles to {DATA}")


if __name__ == "__main__":
    main()
