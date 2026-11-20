"""Make a big pool of random title inputs, one per line.

Usage: python make_pool.py <count> <seed> <out.txt>
Same count + seed always gives the same file.

KeshavKumar's change to the trainer's kit (everything else is unchanged):
  - new EXTRA word bank (weight 4) with families my old 2,000-title exam had and
    this pool did not: dotted capital I, sharp s, Nordic letters, Greek final sigma,
    long s, ligatures, titlecase digraphs, recursive Mc names, more apostrophe,
    title and inline-period forms, underscores.
    Why: SakshiSingh's port is right on all 100,000 titles of the original pool,
    but wrong on 4 of my old 2,000 ('İSTANBUL' loses its dot).
  - three more sub-phrase separators: en dash, figure dash, horizontal bar.
Adding a bank changes the random stream, so this pool differs from the class pool.
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
EXTRA = [
    "\u0130stanbul", "\u0130STANBUL", "GRO\u00df", "\u00f1and\u00fa", "\u00f8resund",
    "\u00c6r\u00f8", "\u00feorn", "\u039f\u0394\u039f\u03a3", "\u03bf\u03b4\u03bf\u03c2",
    "\u017ftar", "\ufb01le", "\ufb02ow", "\u01c6ungla", "\u01c5emal", "\u0149",
    "mcdonald-smith", "mc-hammer", "mcdonald/burger", "mcdonald's",
    "o'neil's", "y'all", "l'", "O'NEIL", "Ph.D.", "a.b", "U.S.A.",
    "dR", "mRS", "_under_", "_dream", "Jean-Luc", "w/o", "http://foo",
    "2nd-hand", "x2", "psst", "cwm", "xyz",
]

BANKS = [(SMALL, 25), (NORMAL, 30), (NAMES, 3), (APOS, 3), (TITLES, 3),
         (INITIALS, 3), (DOTTED, 3), (URLS, 2), (SLASH, 3), (HYPHEN, 4),
         (CONSONANT, 3), (MIXED, 3), (UNICODE, 3), (EXTRA, 4)]
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
                parts.append(rng.choice([": ", ". ", "; ", "? ", "! ", " - ", " \u2014 ",
                                         " \u2013 ", " \u2012 ", " \u2015 "]))
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
            if t in seen or "\n" in t or "\r" in t:
                continue
            seen.add(t)
            f.write(t + "\n")


if __name__ == "__main__":
    main()
