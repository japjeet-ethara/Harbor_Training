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
PUNCT = list("!\"#$%&'()*+,-./:;?@[\\]_`{|}~") + ["\u201c", "\u2018", "\u2013", "\u2014"]
SPACES = [" "] * 20 + ["  ", "\t", "\u00a0", "\u2009"]

# --- Added by Satyam Pandey (Day 5): word families that neither the trainer pool nor
# my old 2,000-title exam had. Each targets a place where a Go port can drift from
# Python: case mappings that change length (U+FB01 -> "FI", U+0130 lower -> 2 runes),
# title-case digraphs (U+01C5), combining marks (\w for `regex`), curly-quote
# possessives, non-ASCII digits, emoji, and rarer Unicode whitespace.
EXTRA = ["\u0130stanbul", "\ufb01nance", "\u01c5ungla", "e\u0301lan", "nasa\u2019s",
         "o\u2019neil", "rock\u2019n\u2019roll", "\u0663rd", "\U0001f680launch",
         "caf\u00e9-bar", "\u00bdprice", "x\u00b2", "\u2160", "co\u00f6perate",
         "\u1e9eTRASSE", "\u00df", "mc\u00e9", "o'\u00e9", "dr.who", "St.", "ltd."]
RARE_SPACES = ["\u2003", "\u202f", "\u3000", "\x0b", "\x0c", "\u2028", "\u1680"]

BANKS = [(SMALL, 25), (NORMAL, 30), (NAMES, 3), (APOS, 3), (TITLES, 3),
         (INITIALS, 3), (DOTTED, 3), (URLS, 2), (SLASH, 3), (HYPHEN, 4),
         (CONSONANT, 3), (MIXED, 3), (UNICODE, 3), (EXTRA, 3)]
WORD_BANKS = [b for b, _ in BANKS]
WEIGHTS = [w for _, w in BANKS]


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
            elif rng.random() < 0.02:            # added: rarer Unicode whitespace
                parts.append(rng.choice(RARE_SPACES))
            else:
                parts.append(rng.choice(SPACES))
    text = "".join(parts)
    if rng.random() < 0.10:
        text = text.upper()
    r = rng.random()                             # added: leading / trailing whitespace
    if r < 0.015:
        text = rng.choice([" ", "  ", "\t", " "]) + text
    elif r < 0.03:
        text = text + rng.choice([" ", "  ", "\t", " "])
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
