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

# --- Day 5 extension: word families missing from the old 2,000-title exam ---
# Contractions and possessives, ASCII and typographic. APOS_SECOND only accepts
# ' and \u2018 after d/l/o, so \u2019 forms take the ordinary path.
CONTRACTIONS = ["don't", "it's", "rock'n'roll", "'90s", "children's",
                "don\u2019t", "it\u2019s", "o\u2019neil", "d\u2019arcy", "l\u2019amour", "\u201990s"]
# Punctuation and symbols outside titlecase's PUNCT set (CAPFIRST does not skip them).
OUTSIDE_PUNCT = ["\u00abparis\u00bb", "\u201ewort\u201c", "\u00bfqu\u00e9", "\u00a1viva",
                 "\u2026later", "<html>", "x=y", "2^10", "\u201dquoted\u201d", "\u2039note\u203a"]
# Symbols, and emoji outside the Basic Multilingual Plane (4-byte UTF-8).
SYMBOLS = ["C++", "C#", "AT&T", "R&D", "Q&A", "\u00a92024", "\u2122", "\u20ac5", "\u2192",
           "\u2605", "\U0001F680", "\u2615", "\U0001F389", "caf\u00e9\u2615"]
# Numbers: no-letter tokens, ordinals and letter+digit words.
NUMBERS = ["2024", "1984", "100%", "#1", "$5", "24/7", "9-to-5", "3.14", "4k", "mp3",
           "1990s", "21st", "2nd", "x86", "b2b", "covid-19"]
# Case mappings that change length or are language-specific (ligatures, dotted I, capital sharp s).
SPECIAL_CASE = ["\ufb01nal", "\ufb02ight", "o\ufb03ce", "\u0130zmir", "\u0130STANBUL", "STRA\u1e9eE"]
# Non-ASCII words with internal capitals (UC_ELSEWHERE is ASCII-only in re mode).
NONASCII_MIXED = ["\u00e9lanVital", "\u00fcberCool", "na\u00efveBayes", "Pok\u00e9Dex",
                  "\u00e7aVa", "\u00c9coleNormale"]
# URLs and paths with hyphens but no period: the slash rule skips them, the hyphen rule splits them.
URL_HYPHEN = ["http://local-host/x-y", "file://c-drive", "ftp://my-box/a-b"]
# Pairs joined by other Unicode spaces (titlecase splits on them) or by a
# zero-width space (not whitespace, so the pair stays one word).
SPACED = ["tokyo\u3000tower", "100\u202f%", "en\u2002route", "math\u205fmode", "zero\u200bwidth"]

BANKS = [(SMALL, 25), (NORMAL, 30), (NAMES, 3), (APOS, 3), (TITLES, 3),
         (INITIALS, 3), (DOTTED, 3), (URLS, 2), (SLASH, 3), (HYPHEN, 4),
         (CONSONANT, 3), (MIXED, 3), (UNICODE, 3)]
BANKS += [(CONTRACTIONS, 3), (OUTSIDE_PUNCT, 2), (SYMBOLS, 2), (NUMBERS, 3),
          (SPECIAL_CASE, 2), (NONASCII_MIXED, 2), (URL_HYPHEN, 1), (SPACED, 2)]
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
