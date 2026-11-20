"""Make a big pool of random title inputs, one per line.

Usage: python make_pool.py <count> <seed> <out.txt>
Same count + seed always gives the same file.

Ashish's additions to the trainer's kit are marked "added:". They cover word
families that my old 2,000-line exam (task/tests/gen.py) never produced at all:
inner "@", digits and ordinals, all-caps hyphenated acronyms, special-casing
characters whose upper/title case changes length, decomposed (NFD) accents,
underscore words, "//", and lines with leading/trailing or no content.
"""
import random
import sys

SMALL = "a an and as at but by en for if in of on or the to v v. via vs vs.".split()
NORMAL = ("lord rings story night city river music data world house light game "
          "history guide life love war peace code book time road heart dream "
          "star ocean garden machine island winter summer").split()
NAMES = ["mcdonald", "McDonald", "MCDONALD", "macintosh", "Mcx", "mcgraw-hill"]
APOS = ["d'arcy", "o'neil", "l'amour", "D'Angelo", "o'reilly's", "l\u2018oiseau"]
TITLES = ["mr", "Mrs", "MS", "dr", "Dr", "mrs."]
INITIALS = ["A.B.", "U.S.", "J.R.R.", "X.", "A.B.C"]
DOTTED = ["example.com", "node.js", "v1.2", "e.g.", "i.e.", "www.site.org"]
URLS = ["http://example.com/a/b", "https://x.org", "ftp://host/file"]
SLASH = ["and/or", "his/her", "input/output", "a/b/c", "TCP/IP"]
HYPHEN = ["self-made", "step-by-step", "x-ray", "re-enter", "out-of-date", "-lead"]
CONSONANT = ["xkcd", "nth", "st", "BBC", "rhythm", "crwth", "pdf"]
MIXED = ["iPhone", "eBay", "macOS", "JavaScript", "gTLD", "McAfee"]
UNICODE = ["\u00e9lan", "\u00fcber", "na\u00efve", "\u00c9cole", "stra\u00dfe",
           "\u0131stanbul", "\u03b1lpha", "\u0434\u043e\u043c"]

# added: an inner "@" never appeared in the old exam, and it is the one shape
# that makes UC_ELSEWHERE / CAPFIRST disagree about where the first word
# character is.
EMAILS = ["ada@example.com", "DEV@nasa.gov", "qa@example.com", "a@b.c",
          "editor@html.test"]
# added: digits. The old exam had "3rd"/"34th" only inside two fixed strings.
NUMBERS = ["3rd", "34th", "2ND", "1st", "42", "0.5", "1,000", "v2", "mp3", "7"]
# added: all-caps hyphenated acronyms. The handout's failure table shows a port
# printing "X-RAY" where the original gives "X-Ray".
ACROHYPH = ["X-RAY", "E-MAIL", "T-SHIRT", "A-1", "UTF-8", "COVID-19", "PPPoE"]
# added: characters whose upper/title case is not one-to-one. Python's str.upper
# turns "\ufb01" into "FI" and "\u0149" into "\u02bcN"; Go's unicode.ToUpper
# leaves both alone. Nothing like this existed in the old exam.
SPECIALCASE = ["\ufb01le", "\ufb02ow", "\u0149t", "\u0130stanbul", "\u01c5ena",
               "\u00dfeta", "\u1e9ees"]
# added: the same accents as UNICODE but decomposed (NFD), so a port that
# indexes bytes or assumes one rune per character behaves differently.
DECOMPOSED = ["e\u0301cole", "u\u0308ber", "nai\u0308ve", "a\u030angstrom",
              "c\u0327edilla"]
# added: "_" is a word character for Python's \w but is also inside PUNCT, so
# CAPFIRST's lazy class makes the two readings disagree. The handout calls out
# "_dream" directly.
UNDERSCORE = ["_dream", "snake_case", "__init__", "a_b", "_"]
# added: "//" is the one case the original's slash branch deliberately skips.
DOUBLESLASH = ["foo//bar", "a//b", "//lead", "trail//", "and/or/not"]

PUNCT = list("!\"#$%&'()*+,-./:;?@[\\]_`{|}~") + ["\u201c", "\u2018", "\u2013", "\u2014"]
SPACES = [" "] * 20 + ["  ", "\t", "\u00a0", "\u2009"]

BANKS = [(SMALL, 25), (NORMAL, 30), (NAMES, 3), (APOS, 3), (TITLES, 3),
         (INITIALS, 3), (DOTTED, 3), (URLS, 2), (SLASH, 3), (HYPHEN, 4),
         (CONSONANT, 3), (MIXED, 3), (UNICODE, 3),
         # added banks
         (EMAILS, 2), (NUMBERS, 3), (ACROHYPH, 2), (SPECIALCASE, 2),
         (DECOMPOSED, 2), (UNDERSCORE, 2), (DOUBLESLASH, 2)]
WORD_BANKS = [b for b, _ in BANKS]
WEIGHTS = [w for _, w in BANKS]

# added: whitespace that can start or end a whole line. The old exam always
# began and ended a line with a word character.
EDGE_SPACES = [" ", "  ", "\t", "\u00a0", "\u2009"]


def word(rng):
    w = rng.choice(rng.choices(WORD_BANKS, WEIGHTS)[0])
    r = rng.random()
    if r < 0.08:
        w = w.upper()
    elif r < 0.12:
        w = w.capitalize()
    if rng.random() < 0.07:
        w = rng.choice(PUNCT) + w
    if rng.random() < 0.10:
        w = w + rng.choice(PUNCT)
    return w


def line(rng):
    n = rng.randint(1, 9)
    parts = []
    for i in range(n):
        parts.append(word(rng))
        if i < n - 1:
            if rng.random() < 0.06:
                parts.append(rng.choice([": ", ". ", "; ", "? ", "! ", " - ", " \u2014 "]))
            else:
                parts.append(rng.choice(SPACES))
    text = "".join(parts)
    # added: leading and trailing whitespace, and the all-whitespace / empty
    # line. splitWS and the small-first/small-last rules all behave differently
    # when the line does not start or end on a word.
    if rng.random() < 0.04:
        text = rng.choice(EDGE_SPACES) + text
    if rng.random() < 0.04:
        text = text + rng.choice(EDGE_SPACES)
    if rng.random() < 0.002:
        text = rng.choice(["", " ", "\t", "\u00a0"])
    if rng.random() < 0.10:
        text = text.upper()
    return text


def main():
    count, seed, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
    rng = random.Random(seed)
    seen = set()
    with open(out, "w", encoding="utf-8") as f:
        while len(seen) < count:
            t = line(rng)
            if t in seen or "\n" in t or "\r" in t:
                continue
            seen.add(t)
            f.write(t + "\n")


if __name__ == "__main__":
    main()