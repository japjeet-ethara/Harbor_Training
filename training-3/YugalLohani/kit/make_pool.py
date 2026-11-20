"""Make a big pool of random title inputs, one per line.

Usage: python make_pool.py <count> <seed> <out.txt>
Same count + seed always gives the same file.

This is the trainer's kit generator with extra word families added, as the
Day 5 guide (section 5.3) directs: "Ask the agent to add word families that
your old inputs never had. Look at the failure table in section 1 for ideas."
The families below bias the pool toward inputs that exercise the real
titlecase rules (mixed inner caps, Mc/Mac, apostrophes, all-consonant
acronyms, inline periods, hyphen/slash parts, embedded all-caps, Unicode
full-case, non-space whitespace). Answers are still frozen from the original
program by answers.py, so nothing here is hand-written.
"""
import random
import sys

# Plain words (naive "capitalize each word" already gets these right).
SMALL = "a an and as at but by en for if in of on or the to v v. via vs vs.".split()
NORMAL = ("lord rings story night city river music data world house light game "
          "history guide life love war peace code book time road heart dream "
          "star ocean garden machine island winter summer").split()

# Rule-breaking families: a naive port is wrong on these.
NAMES = ["mcdonald", "McDonald", "MCDONALD", "macintosh", "Mcx", "mcgraw-hill",
         "mckinsey", "MacArthur", "mcleod", "o'mcduff", "mcx-", "McQ", "mc"]
APOS = ["d'arcy", "o'neil", "l'amour", "D'Angelo", "o'reilly's", "l\u2018oiseau",
        "o'brien", "d'artagnan", "l'enfant", "O'HARA", "d'souza", "l'oreal"]
TITLES = ["mr", "Mrs", "MS", "dr", "Dr", "mrs.", "ms", "mr.", "dr."]
INITIALS = ["A.B.", "U.S.", "J.R.R.", "X.", "A.B.C", "U.S.A.", "F.B.I.", "p.m."]
DOTTED = ["example.com", "node.js", "v1.2", "e.g.", "i.e.", "www.site.org",
          "v._", "a.b", "file.tar.gz", "x.y.z", "v2.0", "3.14"]
URLS = ["http://example.com/a/b", "https://x.org", "ftp://host/file",
        "https://GitHub.com/x", "http//x"]
SLASH = ["and/or", "his/her", "input/output", "a/b/c", "TCP/IP", "either/or",
         "km/h", "n/a", "read/write", "//root"]
HYPHEN = ["self-made", "step-by-step", "x-ray", "re-enter", "out-of-date",
          "-lead", "mother-in-law", "X-RAY", "co-op", "well-known", "a-b",
          "end-to-end", "twenty-one", "-dream", "_dream"]
CONSONANT = ["xkcd", "nth", "st", "BBC", "rhythm", "crwth", "pdf", "html", "css",
             "xml", "json", "sql", "tcp", "www", "ftp", "gnu"]
MIXED = ["iPhone", "eBay", "macOS", "JavaScript", "gTLD", "McAfee", "iOS",
         "eBook", "PhD", "LaTeX", "DVDs", "iPad", "YouTube", "PlayStation"]
UNICODE = ["\u00e9lan", "\u00fcber", "na\u00efve", "\u00c9cole", "stra\u00dfe",
           "\u0131stanbul", "\u03b1lpha", "\u0434\u043e\u043c", "\ufb01sh",
           "\u00dfeta", "\u0130stanbul", "cliche\u0301", "\u01c6ungla",
           "\u212aelvin", "\u017foo", "\u00e6ther", "\u0153uvre"]
# Whole words that are already upper case; in a non-all-caps line titlecase
# preserves them (UC_ELSEWHERE) but a naive port lower-cases the tail.
EMBED_CAPS = ["NASA", "FBI", "CEO", "USA", "OF", "THE", "AT", "IBM", "HTML", "AI"]

PUNCT = list("!\"#$%&'()*+,-./:;?@[\\]_`{|}~") + ["\u201c", "\u2018", "\u2013", "\u2014"]
SPACES = [" "] * 14 + ["  ", "   ", "\t", "\u00a0", "\u2009", "\u2003"]

# Hard families dominate so almost every line breaks a naive port, while a
# minority of plain words keeps ordinary sentences in the mix.
BANKS = [(SMALL, 6), (NORMAL, 6), (NAMES, 9), (APOS, 9), (TITLES, 4),
         (INITIALS, 7), (DOTTED, 10), (URLS, 3), (SLASH, 7), (HYPHEN, 10),
         (CONSONANT, 10), (MIXED, 12), (UNICODE, 10), (EMBED_CAPS, 7)]
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
