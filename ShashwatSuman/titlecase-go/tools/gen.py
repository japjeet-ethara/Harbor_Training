"""Generate the visible and hidden answer sheets for the titlecase-go task.

Run from the titlecase-go folder:

    uv run --no-project --python 3.12 --with regex==2026.11.18 python tools/gen.py

It writes four files into tests/data/ and copies the visible pair into
environment/examples/ so the agent has examples to work from:

    inputs.txt / expected.txt                 visible set (2000 lines)
    hidden_inputs.txt / hidden_expected.txt   hidden set  (2000 lines, never shown to the agent)

The expected answers are never written by hand: every one comes from running
the ORIGINAL Python titlecase() from ../python-titlecase.

This file lives in tools/, not tests/, on purpose: Reward Kit treats every
.py file in tests/ as a scoring check, and the agent must never see it.
"""

import random
import shutil
import sys
from pathlib import Path

TASK_DIR = Path(__file__).resolve().parent.parent
REPO_DIR = TASK_DIR.parent / "python-titlecase"
DATA_DIR = TASK_DIR / "tests" / "data"
EXAMPLES_DIR = TASK_DIR / "environment" / "examples"

sys.path.insert(0, str(REPO_DIR))
import titlecase as tc_module  # noqa: E402
from titlecase import titlecase  # noqa: E402

# The library silently falls back to Python's `re` when `regex` is missing,
# and that fallback gives different answers. The task is defined against the
# `regex` behaviour, so refuse to run without it.
if not tc_module.REGEX_AVAILABLE:
    sys.exit("The `regex` package is not installed. Run with: --with regex==2026.11.18")

N_PER_SET = 2000

# ---------------------------------------------------------------- word pools
NORMAL = """
lord rings return king fellowship towers hobbit dragon river mountain city night
day light dark story history guide manual cooking garden house life death love
war peace time space journey road home world ocean forest island machine future
past secret code music song dance heart mind dream winter summer spring autumn
fire water earth wind stone glass iron gold silver shadow empire republic
kingdom quest legend myth hero villain friend enemy family school teacher
student doctor lawyer engineer artist writer reader programmer data science
art theory practice method system design pattern network computer language
python golang rust java coffee tea bread wine apple orange banana cherry
""".split()

SMALL = ["a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in", "of",
         "on", "or", "the", "to", "v", "v.", "via", "vs", "vs."]

ACRONYMS = ["NASA", "FBI", "CIA", "USA", "UK", "HTML", "CSS", "API", "SQL", "BBC",
            "IBM", "NATO", "UNESCO", "CEO", "DIY", "FAQ", "GPU", "CPU", "AI"]

CONSONANT_WORDS = ["pfft", "psst", "nth", "st", "cwm", "brr", "hmm", "shh", "tsk",
                   "grr", "pst", "mm", "bcd", "XYZ", "nbc", "CNN", "dvd", "tv"]

MAC_WORDS = ["mcdonald", "McDonald", "MCDONALD", "mcintosh", "macintosh",
             "McGraw-hill", "mcthe", "mca", "mcx", "Mc", "mc", "MCA", "mcdonald's",
             "mc-hammer", "mcCarthy", "mcd.com", "mcélan", "mc_test"]

APOS_WORDS = ["d'artagnan", "D'Artagnan", "o'neil", "O'NEIL", "o'neill's", "l'oreal",
              "L'Oréal", "o‘brien", "d‘angelo", "l'été", "o'straße", "d'x", "o's",
              "d'ad's", "l'a''", "o'neil'ss", "don't", "can't", "rock'n'roll", "'tis",
              "o'", "d''", "ol'", "l'ÿ"]

TITLES = ["mr", "mrs", "ms", "dr", "MR", "Mrs", "DR", "Ms", "mr.", "dr.", "mrs.", "drs"]

INITIALS = ["U.S.", "U.K.", "J.R.R.", "A.B.C.", "U.S.A.", "E.U", "A.B", "J.", "j.r.",
            "U.s.", "A..", "A.BC."]

INLINE = ["example.com", "www.python.org", "e.g.", "i.e.", "node.js", "v1.2",
          "file.txt", "a.b", "foo.Bar", "x.y.z", "étoile.été"]

CAMEL = ["iPhone", "eBay", "macOS", "iOS", "YouTube", "JavaScript", "PowerPoint",
         "mySQL", "jQuery", "GitHub", "LaTeX", "ÉCOLE", "éCole", "McKinsey", "x2Y"]

SLASH_HYPHEN = ["and/or", "this/that", "in/out", "self-driving", "the-end",
                "e-mail", "up-to-date", "x-ray", "on-the-go", "3-d", "a-z",
                "http://example.com/path", "https://foo.org/a/b", "/usr/bin",
                "either/or-not", "the/a", "mother-in-law", "-dash", "slash/",
                "co-op/the", "a//b", "-", "/", "--", "ÉTÉ-été"]

ACCENTED = ["élan", "über", "ñandú", "straße", "ÿes", "àla", "café", "naïve",
            "résumé", "Zürich", "øresund", "ångström", "çava", "ßeta", "ÉCLAIR",
            "ÆON", "þorn", "ðe", "ìtaly", "ôtel"]

NUMBERS = ["2nd", "1990s", "101", "3rd", "4th", "42", "2024", "1st", "100%",
           "$5", "#1", "v2", "x86", "mp3", "b2b"]

OTHER = ["snake_case", "_private", "__init__", "hello_World", "a_b", "foo's",
         "it's", "won't", "rock’n’roll", "it’s"]

PUNCT_PREFIX = ['"', "(", "'", "“", "‘", "[", "{", "*", "_", "-", "–", "—", "¿", "¡",
                "...", "#", "@", "~", "`", "«", "<", "’"]
PUNCT_SUFFIX = ['"', ")", "'", "”", "’", "]", "}", ".", ",", "!", "?", ":", ";",
                "...", "!?", "»", ">", "-", "–", "—", "―", "‒"]
SUBPHRASE_SEPS = [":", ".", ";", "?", "!", "-", "–", "‒", "—", "―"]

RARE_POOLS = [ACRONYMS, CONSONANT_WORDS, MAC_WORDS, APOS_WORDS, TITLES, INITIALS,
              INLINE, CAMEL, SLASH_HYPHEN, ACCENTED, NUMBERS, OTHER]


def rand_case(word: str) -> str:
    r = random.random()
    if r < 0.55:
        return word
    if r < 0.70:
        return word.upper()
    if r < 0.85:
        return word.capitalize()
    if r < 0.95:
        return word.lower()
    return "".join(c.upper() if random.random() < 0.5 else c for c in word)


def pick_word() -> str:
    r = random.random()
    if r < 0.40:
        w = random.choice(NORMAL)
    elif r < 0.65:
        w = random.choice(SMALL)
    else:
        w = random.choice(random.choice(RARE_POOLS))
    w = rand_case(w) if random.random() < 0.5 else w
    if random.random() < 0.08:
        w = random.choice(PUNCT_PREFIX) + w
    if random.random() < 0.10:
        w = w + random.choice(PUNCT_SUFFIX)
    return w


def make_title() -> str:
    n = random.choice([1, 1, 2, 3, 3, 4, 4, 5, 5, 6, 7, 8, 10, 12])
    parts = [pick_word() for _ in range(n)]
    # Sub-phrases: "title: a subtitle", "part one - the start"
    if n >= 3 and random.random() < 0.30:
        i = random.randrange(1, n)
        parts[i - 1] = parts[i - 1] + random.choice(SUBPHRASE_SEPS)
        parts[i] = random.choice(SMALL + ["an", "the", "and", "android", "vs.x"])
    if n >= 3 and random.random() < 0.08:
        i = random.randrange(1, n)
        parts.insert(i, random.choice(SUBPHRASE_SEPS))
    seps = [random.choice([" "] * 12 + ["  ", "   "]) for _ in range(len(parts) - 1)]
    out = parts[0]
    for sep, part in zip(seps, parts[1:]):
        out += sep + part
    r = random.random()
    if r < 0.12:
        out = out.upper()            # all-caps lines take a different path
    elif r < 0.20:
        out = out.lower()
    if random.random() < 0.03:
        out = " " + out
    if random.random() < 0.03:
        out = out + " "
    return out


def is_valid(line: str) -> bool:
    # One title per line: no line breaks of any kind, no control characters.
    return all(ch == " " or (ch.isprintable() and not ch.isspace()) for ch in line)


def main() -> None:
    random.seed(1)
    seen: set[str] = set()
    sets: list[list[str]] = [[], []]
    # A few fixed edge cases go first in each set.
    fixed = [
        ["the lord of the rings", "", " ", "a", "THE END", "nasa launches a rocket",
         "title: a subtitle", "straße der stadt"],
        ["of mice and men", "THE", "an", "  ", "U.S. NEWS AND WORLD REPORT",
         "o'neil vs. mcdonald", "über alles: the story", "  leading spaces"],
    ]
    for k in (0, 1):
        for t in fixed[k]:
            if t not in seen:
                seen.add(t)
                sets[k].append(t)
    for k in (0, 1):
        while len(sets[k]) < N_PER_SET:
            t = make_title()
            if t in seen or not is_valid(t):
                continue
            seen.add(t)
            sets[k].append(t)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    names = [("inputs.txt", "expected.txt"), ("hidden_inputs.txt", "hidden_expected.txt")]
    for (inp_name, exp_name), lines in zip(names, sets):
        expected = [titlecase(t) for t in lines]
        for t, e in zip(lines, expected):
            assert "\n" not in e and "\r" not in e, (t, e)
        # newline="\n" so the files are byte-identical on Windows, macOS and Linux.
        with open(DATA_DIR / inp_name, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(lines) + "\n")
        with open(DATA_DIR / exp_name, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(expected) + "\n")

    EXAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(DATA_DIR / "inputs.txt", EXAMPLES_DIR / "inputs.txt")
    shutil.copyfile(DATA_DIR / "expected.txt", EXAMPLES_DIR / "expected.txt")
    print(f"wrote {N_PER_SET} visible + {N_PER_SET} hidden titles to {DATA_DIR}")


if __name__ == "__main__":
    main()
