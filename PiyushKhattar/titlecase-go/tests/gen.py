#!/usr/bin/env python3
"""Generate deterministic titlecase inputs and expected outputs.

Expected lines are produced only by calling the original python-titlecase
``titlecase()`` implementation. This script does not reimplement those rules.
"""

import random
import sys
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
COUNT = 2000

# Single-line inputs quoted in NOTES.md. Multi-line samples are omitted
# because each generated record is one title.
DOCUMENTED = [
    "text\twith\ttabs",
    "of mice and men",
    "D.C.",
    "l'grange",
    "o'grange",
    "mcclelland",
    "dr",
    "this is just an example.com",
    "iTunes should be unmolested",
    "this v that",
    "a title and/or string",
    "end-to-end",
    "THIS IS A TEST",
    "cnn",
    "(hello)",
    "34th",
    "a thing",
    "Small word at end is nothing to be afraid of",
    "Starting Sub-Phrase With a Small Word: a Trick, Perhaps?",
    "Snakes on a Plane — a trick",
    "MCDOWELL",
    "macdonalds",
    "mac mc MAC MC machine",
    "http://foo.com",
    "st",
]

WORDS = [
    "apple", "bridge", "market", "report", "music", "castle", "river",
    "silver", "garden", "window", "letter", "orange", "planet", "copper",
    "forest", "engine", "harbor", "yellow", "purple", "winter", "summer",
    "captain", "village", "history", "science", "picture", "secret",
    "public", "private", "morning", "evening", "central", "foreign",
    "ancient", "modern", "simple", "double", "quiet", "famous", "final",
    "open", "closed", "north", "south", "east", "west", "paper", "stone",
    "glass", "water", "light", "shadow", "cloud", "storm", "field",
]
SMALL = [
    "a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in",
    "of", "on", "or", "the", "to", "v", "v.", "via", "vs", "vs.",
]
ACRONYMS = ["cnn", "html", "gps", "lcd", "sql", "ftp", "nyc", "pdf", "ibm"]
SHORT_CONSONANTS = ["st", "bc", "tv", "pt", "hm"]
ORDINALS = ["1st", "2nd", "3rd", "4th", "5th", "10th", "21st", "34th", "100th"]
MIXED_TOKENS = ["iTunes", "iPhone", "AT&T", "Q&A", "PhD", "JavaScript", "MacDonalds"]
HOSTS = ["example.com", "del.icio.us", "foo.bar", "news.site.org"]
SUBPHRASE_MARKS = [":", ".", ";", "?", "!", "-", "–", "‒", "—", "―"]
LEAD_PUNCT = ["'", "‘", '"', "“", "(", "["]
SPACES = [" ", "\t", "\u00a0", "\u200a", "\u2006"]
APOS_STEMS = ["grange", "clock", "malley", "amour", "angelo", "brian", "neil"]
MC_TAILS = ["clelland", "donald", "tavish", "dowell", "mahon", "gregor", "intosh"]
HONORIFICS = ["mr", "mrs", "ms", "dr", "Mr", "MRS", "Ms", "DR", "Dr"]


def _words(n):
    out = []
    for _ in range(n):
        if random.random() < 0.28:
            out.append(random.choice(SMALL))
        else:
            out.append(random.choice(WORDS))
    return out


def _join(parts):
    sep = random.choice(SPACES) if random.random() < 0.15 else " "
    return sep.join(parts)


def _sentence(n=None):
    n = n if n is not None else random.randint(3, 8)
    words = _words(n)
    style = random.choice(["lower", "title", "upper", "as_is"])
    if style == "upper":
        words = [w.upper() for w in words]
    elif style == "title":
        words = [w.capitalize() for w in words]
    if random.random() < 0.2 and words:
        index = random.randrange(len(words))
        word = words[index]
        if len(word) > 2 and word.isalpha():
            cut = random.randrange(1, len(word))
            words[index] = word[:cut] + word[cut].upper() + word[cut + 1:]
    return _join(words)


def _initials():
    pieces = []
    for _ in range(random.randint(2, 4)):
        if random.random() < 0.5:
            pieces.append(random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ") + ".")
        else:
            pieces.append(
                random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
                + "."
                + random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
            )
    token = "".join(pieces)
    return _join([w.upper() for w in _words(random.randint(2, 4))] + [token])


def _apostrophe():
    letter = random.choice(["d", "l", "o", "D", "L", "O"])
    mark = random.choice(["'", "‘"])
    word = letter + mark + random.choice(APOS_STEMS)
    if random.random() < 0.35:
        word += "'s"
    return _join([word, *_words(random.randint(1, 4))])


def _mc():
    prefix = random.choice(["mc", "Mc", "MC"])
    word = prefix + random.choice(MC_TAILS)
    if random.random() < 0.4:
        word = word.upper()
    return _join([word, *_words(random.randint(1, 3))])


def _honorific():
    return _join([random.choice(HONORIFICS), random.choice(WORDS)])


def _internal_period():
    return _join(_words(random.randint(2, 4)) + [random.choice(HOSTS)])


def _url():
    host = random.choice(["foo", "bar", "example"])
    return _join(_words(random.randint(2, 4)) + [f"http://{host}.com"])


def _hyphen():
    parts = [random.choice(WORDS), random.choice(SMALL), random.choice(WORDS)]
    if random.random() < 0.3:
        parts = [p.upper() for p in parts]
    token = "-".join(parts)
    return _join(_words(random.randint(1, 3)) + [token])


def _slash():
    left = random.choice(WORDS + SMALL)
    right = random.choice(WORDS + SMALL)
    token = f"{left}/{right}"
    if random.random() < 0.3:
        token = token.upper()
    return _join(_words(random.randint(1, 3)) + [token, *_words(random.randint(0, 2))])


def _subphrase():
    mark = random.choice(SUBPHRASE_MARKS)
    return f"{_sentence(random.randint(3, 6))}{mark} {random.choice(SMALL)} {_sentence(random.randint(2, 4))}"


def _leading_small():
    return f"{random.choice(LEAD_PUNCT)}{random.choice(SMALL)} {_sentence(random.randint(2, 5))}"


def _trailing_small():
    return f"{_sentence(random.randint(3, 6))} {random.choice(SMALL)}"


def _acronym():
    word = random.choice(ACRONYMS)
    if random.random() < 0.5:
        word = word.upper()
    return _join(_words(random.randint(2, 4)) + [word, *_words(random.randint(1, 3))])


def _short_consonant():
    return _join(_words(random.randint(1, 3)) + [random.choice(SHORT_CONSONANTS)])


def _ordinal():
    return _join([random.choice(ORDINALS), *_words(random.randint(2, 4))])


def _wrapped():
    word = random.choice(WORDS)
    punct = random.choice(LEAD_PUNCT)
    close = {"'": "'", "‘": "’", '"': '"', "“": "”", "(": ")", "[": "]"}[punct]
    return _join([f"{punct}{word}{close}", *_words(random.randint(1, 3))])


def _mixed_preserve():
    return _join(_words(random.randint(1, 3)) + [random.choice(MIXED_TOKENS), *_words(random.randint(1, 3))])


def _all_caps_mixed_token():
    # An all-capital line skips the "uppercase elsewhere" keep-as-is rule.
    return _join([w.upper() for w in _words(random.randint(2, 5))] + [random.choice(MIXED_TOKENS).upper()])


BUILDERS = [
    _sentence,
    _sentence,
    _sentence,
    _initials,
    _apostrophe,
    _mc,
    _honorific,
    _internal_period,
    _url,
    _hyphen,
    _slash,
    _subphrase,
    _leading_small,
    _trailing_small,
    _acronym,
    _short_consonant,
    _ordinal,
    _wrapped,
    _mixed_preserve,
    _all_caps_mixed_token,
]


def _one_title():
    title = random.choice(BUILDERS)()
    if "\n" in title or "\r" in title:
        raise RuntimeError("generated title contains a line break")
    return title


def _generate(count, seen):
    titles = []
    while len(titles) < count:
        title = _one_title()
        if title in seen:
            continue
        result = titlecase(title)
        if "\n" in result or "\r" in result:
            continue
        seen.add(title)
        titles.append(title)
    return titles


def _write(path, lines):
    path.write_text("".join(line + "\n" for line in lines), encoding="utf-8", newline="\n")


def main():
    random.seed(1)
    original_repo = Path(__file__).resolve().parents[2] / "python-titlecase"
    sys.path.insert(0, str(original_repo))
    import titlecase as titlecase_module
    from titlecase import titlecase

    source = Path(titlecase_module.__file__).resolve()
    if source != (original_repo / "titlecase" / "__init__.py").resolve():
        raise SystemExit(f"Refusing to use a non-original titlecase: {source}")
    if not titlecase_module.REGEX_AVAILABLE:
        raise SystemExit(
            "The original titlecase package imported the re fallback. "
            "Install the optional 'regex' package so titlecase() uses its Unicode rules."
        )
    globals()["titlecase"] = titlecase

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    seen = set()
    public = []
    for title in DOCUMENTED:
        if title in seen:
            continue
        result = titlecase(title)
        if "\n" in title or "\r" in title or "\n" in result or "\r" in result:
            raise SystemExit(f"documented title is not a single line: {title!r} -> {result!r}")
        seen.add(title)
        public.append(title)
    public.extend(_generate(COUNT - len(public), seen))
    hidden = _generate(COUNT, seen)

    public_expected = [titlecase(title) for title in public]
    hidden_expected = [titlecase(title) for title in hidden]

    _write(DATA_DIR / "inputs.txt", public)
    _write(DATA_DIR / "expected.txt", public_expected)
    _write(DATA_DIR / "hidden_inputs.txt", hidden)
    _write(DATA_DIR / "hidden_expected.txt", hidden_expected)


if __name__ == "__main__":
    main()
