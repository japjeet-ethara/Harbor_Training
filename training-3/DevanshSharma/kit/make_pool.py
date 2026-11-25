"""make_pool.py <count> <seed> <out.txt>

Generate <count> unique, deterministic titles into <out.txt>.
Run with: python -I make_pool.py 100000 1 pool.txt
"""
import random
import sys
from pathlib import Path

COUNT = int(sys.argv[1])
SEED  = int(sys.argv[2])
OUT   = Path(sys.argv[3])

# Large, diverse word list – covers every rule the Go port must implement.
WORDS = [
    # small words
    "the", "of", "and", "a", "an", "in", "on", "to", "for", "but", "or", "nor",
    "vs.", "vs", "v", "v.", "via", "as", "at", "by", "en", "if",
    # acronyms / initialisms
    "NASA", "CNN", "HTML", "AT&T", "Q&A", "BBC", "TCP/IP", "PPPoE", "U.S.A.", "D.C.",
    "FBI", "CIA", "MLB", "NFL",
    # Apple-style camel case
    "iPhone", "iTunes", "macOS", "iOS",
    # Mc/MC names
    "mcdonald", "McDonalds", "mcfoo", "MCHammer", "McDonald",
    # d'/o'/l' apostrophes
    "O'Neil", "o'reilly", "l'grange", "d'Angelo", "O'Brien",
    # Mr/Mrs/Ms/Dr
    "Mr", "Mrs", "Ms", "Dr", "dr.", "mr",
    # inline period / domain
    "example.com", "del.icio.us", "e.g", "i.e", "U.S",
    # URLs
    "http://example.com/x", "https://en.wikipedia.org/wiki/Title_case", "http://foo.com",
    # ordinals / numbers
    "3rd", "34th", "5th", "21st", "v1.2", "v2.0",
    # e-mail / hyphen compounds
    "e-mail", "end-to-end", "state-of-the-art", "well-known",
    # slash compounds
    "and/or", "foo//bar", "TCP/IP",
    # all-consonant acronyms
    "gym", "rhythm", "St", "rhythm", "nfl", "cnn",
    # misc
    "nino", "cafe", "STATE", "episode", "EPISODE", "(the)",
    # tricky separators
    "v._ music!", "world - d'arcy", "X. TCP/IP",
    # non-ASCII edge cases (covered by stdlib re mode)
    "istanbul", "Mcx-", "_dream",
]

SEPARATORS = [": ", "; ", ". ", "? ", "! ", " - ", " — ", " – ", " / "]

FIXED = [
    "the lord of the rings",
    "a title and/or string",
    "nothing to be afraid of",
    "this v. that",
    "this vs. that",
    "EPISODE 7 — THE FORCE AWAKENS",
    "Words with all consonants like cnn",
    "mac mc MAC MC machine",
    "WASHINGTON, D.C. SHOULD BE FIXED",
    "BBC: OF at Mcx- if summer time by",
    "v._ music! world - d'arcy",
    "X. TCP/IP history as! X-RAY",
    "Mr. Smith goes to washington",
    "the quick brown fox",
    "O'Brien's last stand",
    "l'Amour perdu",
    "AT&T and the BBC",
    "iPhone vs. Android",
    "Dr. Jekyll and Mr. Hyde",
    "end-to-end encryption",
    "foo//bar baz",
    "and/or neither",
    "mcdonald's farm",
    "Mc hammer time",
    "d'Angelo sings",
    "THE QUICK BROWN FOX JUMPS OVER THE LAZY DOG",
    "u.s.a. in the morning",
    "e-mail from dr. smith",
    "nothing: nothing",
    "tabs\there",
]


def make_title(rng: random.Random) -> str:
    kind = rng.randrange(16)
    if kind == 0:
        title = " ".join(rng.choice(WORDS) for _ in range(rng.randint(1, 9)))
    elif kind == 1:
        title = " ".join(rng.choice(WORDS) for _ in range(rng.randint(2, 8))).upper()
    elif kind == 2:
        left = rng.choice(WORDS)
        right = rng.choice(WORDS)
        title = f"{left}-{right}"
        if rng.randrange(2) == 0:
            title = f"{title}-{rng.choice(WORDS)}"
    elif kind == 3:
        title = f"{rng.choice(WORDS)}/{rng.choice(WORDS)}"
    elif kind == 4:
        title = rng.choice(SEPARATORS).join(
            rng.choice(WORDS) for _ in range(rng.randint(2, 4))
        )
    elif kind == 5:
        title = f"{rng.choice(['O', 'o', 'L', 'l', 'D'])}'{rng.choice(['neil', 'grange', 'angelo', 'Reilly', 'Brien'])}"
    elif kind == 6:
        title = f"{rng.choice(['Mr', 'mr', 'Mrs', 'Ms', 'Dr', 'dr', 'Mc', 'mc', 'MC'])} {rng.choice(WORDS)}"
    elif kind == 7:
        title = f"{rng.choice(WORDS)}  {rng.choice(WORDS)}\t{rng.choice(WORDS)}"
    elif kind == 8:
        title = f"({rng.choice(WORDS)}) {rng.choice(WORDS)}?"
    elif kind == 9:
        title = f"{rng.choice(['http://foo.com', 'example.com', 'iTunes', 'AT&T', 'Q&A', 'e.g'])} {rng.choice(WORDS)}"
    elif kind == 10:
        title = f"{rng.choice(WORDS)} of the {rng.choice(WORDS)}"
    elif kind == 11:
        title = rng.choice(FIXED)
    elif kind == 12:
        # version-number words like v1.2
        title = f"v{rng.randint(1,9)}.{rng.randint(0,9)} {rng.choice(WORDS)}"
    elif kind == 13:
        # leading underscore / non-alpha prefix
        title = f"_{rng.choice(WORDS)} {rng.choice(WORDS)}"
    elif kind == 14:
        # multi-word ALL CAPS phrase
        title = " ".join(rng.choice(WORDS) for _ in range(rng.randint(3, 6))).upper()
    else:
        # mixed separators: colon + subphrase
        sep = rng.choice([": ", "; ", "! ", "? ", ". "])
        title = rng.choice(WORDS) + sep + " ".join(rng.choice(WORDS) for _ in range(rng.randint(1, 4)))

    return title.replace("\n", " ").replace("\r", " ")


def main() -> None:
    rng = random.Random(SEED)
    seen: set[str] = set()
    titles: list[str] = []
    attempts = 0
    while len(titles) < COUNT:
        t = make_title(rng)
        attempts += 1
        if t not in seen:
            seen.add(t)
            titles.append(t)
        if attempts > COUNT * 20:
            break
    OUT.write_text("\n".join(titles) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {len(titles)} unique titles to {OUT}", file=sys.stderr)


if __name__ == "__main__":
    main()
