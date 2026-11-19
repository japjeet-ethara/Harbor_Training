"""Make a big pool of random title inputs, one per line.

Usage: python make_pool.py <count> <seed> <out.txt>
Same count + seed always gives the same file.
"""
import random
import sys

SMALL = "a an and as at but by en for if in of on or the to v v. via vs vs.".split()
NORMAL = ("lord rings story night city river music data world house light game "
          "history guide life love war peace code book time road heart dream "
          "star ocean garden machine island winter summer").split()
NAMES = ["mcdonald", "McDonald", "MCDONALD", "macintosh", "Mcx", "Mcx-", "McX", "mcgraw-hill"]
APOS = ["d'arcy", "o'neil", "l'amour", "D'Angelo", "o'reilly's", "l\u2018oiseau"]
TITLES = ["mr", "Mrs", "MS", "dr", "Dr", "mrs."]
INITIALS = ["A.B.", "U.S.", "J.R.R.", "X.", "A.B.C"]
DOTTED = ["example.com", "node.js", "v1.2", "v2.0.1", "e.g.", "i.e.", "www.site.org"]
URLS = ["http://example.com/a/b", "https://x.org", "ftp://host/file"]
SLASH = ["and/or", "his/her", "input/output", "a/b/c", "TCP/IP"]
HYPHEN = ["self-made", "step-by-step", "x-ray", "X-RAY", "re-enter", "out-of-date", "-lead"]
CONSONANT = ["xkcd", "nth", "st", "BBC", "rhythm", "crwth", "pdf"]
MIXED = ["iPhone", "eBay", "macOS", "JavaScript", "gTLD", "McAfee"]
UNICODE = ["\u00e9lan", "\u00fcber", "na\u00efve", "\u00c9cole", "stra\u00dfe",
           "\u0131stanbul", "\u0130stanbul", "\u03b1lpha", "\u0434\u043e\u043c",
           "\u01c5", "\u01c8", "\ufb01"]
UNDERSCORE = ["_dream", "__init__", "foo_bar", "dream_"]
PUNCT = list("!\"#$%&'()*+,-./:;?@[\\]_`{|}~") + ["\u201c", "\u2018", "\u2013", "\u2014"]
SPACES = [" "] * 20 + ["  ", "\t", "\u00a0", "\u2009", "\u3000"]

BANKS = [(SMALL, 25), (NORMAL, 30), (NAMES, 3), (APOS, 3), (TITLES, 3),
         (INITIALS, 3), (DOTTED, 3), (URLS, 2), (SLASH, 3), (HYPHEN, 4),
         (CONSONANT, 3), (MIXED, 3), (UNICODE, 3), (UNDERSCORE, 3)]
WORD_BANKS = [b for b, _ in BANKS]
WEIGHTS = [w for _, w in BANKS]
LINE_SPLITS = ("\r", "\n", "\v", "\f", "\x1c", "\x1d", "\x1e", "\x85", "\u2028", "\u2029")


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
            if t in seen or any(c in t for c in LINE_SPLITS):
                continue
            seen.add(t)
            f.write(t + "\n")


if __name__ == "__main__":
    main()
