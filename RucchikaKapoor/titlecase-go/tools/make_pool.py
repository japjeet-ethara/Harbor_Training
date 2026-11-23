"""Make a large pool of varied title inputs, one per line.

Usage: python make_pool.py <count> <seed> <out.txt>
"""
import random
import sys

SMALL = "a an and as at but by en for if in of on or the to v v. via vs vs.".split()
NORMAL = (
    "lord rings story night city river music data world house light game "
    "history guide life love war peace code book time road heart dream "
    "star ocean garden machine island winter summer"
).split()
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
UNICODE = [
    "\u00e9lan", "\u00fcber", "na\u00efve", "\u00c9cole", "stra\u00dfe",
    "\u0131stanbul", "\u03b1lpha", "\u0434\u043e\u043c",
]
PUNCT = list("!\"#$%&'()*+,-./:;?@[\\]_`{|}~") + [
    "\u201c", "\u2018", "\u2013", "\u2014",
]
SPACES = [" "] * 20 + ["  ", "\t", "\u00a0", "\u2009"]

BANKS = [
    (SMALL, 25), (NORMAL, 30), (NAMES, 3), (APOS, 3), (TITLES, 3),
    (INITIALS, 3), (DOTTED, 3), (URLS, 2), (SLASH, 3), (HYPHEN, 4),
    (CONSONANT, 3), (MIXED, 3), (UNICODE, 3),
]
WORD_BANKS = [bank for bank, _ in BANKS]
WEIGHTS = [weight for _, weight in BANKS]


def word(rng):
    value = rng.choice(rng.choices(WORD_BANKS, WEIGHTS)[0])
    case = rng.random()
    if case < 0.08:
        value = value.upper()
    elif case < 0.12:
        value = value.capitalize()
    if rng.random() < 0.07:
        value = rng.choice(PUNCT) + value
    if rng.random() < 0.10:
        value += rng.choice(PUNCT)
    return value


def line(rng):
    count = rng.randint(1, 9)
    parts = []
    for index in range(count):
        parts.append(word(rng))
        if index < count - 1:
            if rng.random() < 0.06:
                parts.append(rng.choice([": ", ". ", "; ", "? ", "! ", " - ", " \u2014 "]))
            else:
                parts.append(rng.choice(SPACES))
    text = "".join(parts)
    if rng.random() < 0.10:
        text = text.upper()
    return text


def main():
    count, seed, output_path = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
    rng = random.Random(seed)
    seen = set()
    with open(output_path, "w", encoding="utf-8", newline="\n") as output:
        while len(seen) < count:
            text = line(rng)
            if text in seen or "\n" in text or "\r" in text:
                continue
            seen.add(text)
            output.write(text + "\n")


if __name__ == "__main__":
    main()
