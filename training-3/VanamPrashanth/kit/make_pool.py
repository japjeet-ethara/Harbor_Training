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
# --- Added families (Vanam Prashanth, Day 5): things my old gen.py inputs never had ---
# Right single quote U+2019 (the original only treats ' and U+2018 as apostrophes), contractions.
APOS2 = ["d\u2019arcy", "o\u2019neil", "L\u2019AMOUR", "don't", "it's", "rock'n'roll",
         "o'clock", "children's", "'90s", "D'arcy", "O'NEIL"]
# Words that start with or mix digits.
NUMERIC = ["3d", "21st", "100%", "4x4", "covid-19", "c3po", "2nd-hand", "9-to-5",
           "24/7", "mp3", "1.5", "v2", "x86_64"]
# Roman numerals: some are all consonants (MCMXC), some are not (xiv).
ROMAN = ["ii", "iii", "xiv", "mcmxc", "xxl", "cd", "lv"]
# Hyphen chains with small words inside, and Mc- edge cases from the failure table.
HYPHEN2 = ["mother-in-law", "jack-of-all-trades", "up-to-date", "state-of-the-art",
           "Mcx-", "mcx-", "MC-", "mc-donald", "x-RAY", "-to-", "a-"]
# Symbols, handles, underscores, ellipses, the "v._" case from the failure table.
SYMBOLIC = ["c++", "c#", ".net", "r&d", "#hashtag", "@user", "john@doe.com",
            "snake_case", "__init__", "_dream", "v._", "x.", "\u2026", "...", "--"]
# Harder Unicode: Turkish I, titlecase digraph, ligature, final sigma, combining accent, emoji.
UNICODE2 = ["\u0130zmir", "\u01c5emal", "\ufb01le", "\u039f\u0394\u039f\u03a3",
            "e\u0301cole", "\u00f1and\u00fa", "\u0142\u00f3d\u017a", "\u00c6r\u00f8",
            "\U0001f3b5music", "\u00df", "\u0149"]
# --- end of added families ---
PUNCT = list("!\"#$%&'()*+,-./:;?@[\\]_`{|}~") + ["\u201c", "\u2018", "\u2013", "\u2014",
         "\u201d", "\u2019", "\u00ab", "\u00bb"]  # added: closing curly quotes, guillemets
SPACES = [" "] * 20 + ["  ", "\t", "\u00a0", "\u2009",
                       "\u2002", "\u2003", "\u202f", "\u3000"]  # added: en, em, narrow nbsp, ideographic

BANKS = [(SMALL, 25), (NORMAL, 30), (NAMES, 3), (APOS, 3), (TITLES, 3),
         (INITIALS, 3), (DOTTED, 3), (URLS, 2), (SLASH, 3), (HYPHEN, 4),
         (CONSONANT, 3), (MIXED, 3), (UNICODE, 3),
         (APOS2, 3), (NUMERIC, 3), (ROMAN, 2), (HYPHEN2, 3), (SYMBOLIC, 3), (UNICODE2, 3)]
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
    with open(out, "w", encoding="utf-8", newline="\n") as f:  # LF on Windows too
        while len(seen) < count:
            t = line(rng)
            # one title must stay one line for every reader (Go scanner and Python splitlines)
            if t in seen or "\n" in t or "\r" in t or len(t.splitlines()) != 1:
                continue
            seen.add(t)
            f.write(t + "\n")


if __name__ == "__main__":
    main()
