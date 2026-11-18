"""Generate deterministic titlecase fixtures from the original Python library.

Expected files are produced only by calling titlecase(). Do not hand-write them.
"""

import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY_REPO = ROOT.parent / "python-titlecase"
sys.path.insert(0, str(PY_REPO))

from titlecase import titlecase  # noqa: E402

DATA = ROOT / "tests" / "data"
COUNT = 2000

# Characters that would split a fixture line, including Unicode line breaks.
LINE_BREAKS = set("\n\r\v\f\x1c\x1d\x1e\x85\u2028\u2029")

# Inputs drawn from NOTES.md and the original test suite. Newlines are omitted
# because each fixture line is one title.
CANONICAL = [
    "a simple tcp and udp wrapper",
    "WASHINGTON, D.C. SHOULD BE FIXED BUT MIGHT BE A PROBLEM",
    "o'grange",
    "mcdonald",
    "mr smith",
    "this is just an example.com",
    "this is a TEST",
    "this v that",
    "word/word",
    "end-to-end",
    "THIS IS ALL CAPS AND SHOULD BE ADDRESSED",
    "words like cnn",
    "a thing",
    "by the sea",
    "nothing to be afraid of",
    "Starting Sub-Phrase With a Small Word: a Trick, Perhaps?",
    "text\twith\ttabs",
    "a title and/or string",
    "dance with me/let’s face the music and dance",
    "a-b end-to-end two-not-three/three-by-four/five-and",
    "34th 3rd 2nd",
    "Q&A with steve jobs: 'that's what happens in technology'",
    "What is AT&T's problem?",
    "Apple deal with AT&T falls through",
    "this v. that",
    "this vs that",
    "this vs. that",
    "The SEC's Apple probe: what you need to know",
    "'by the Way, small word at the start but within quotes.'",
    "Small word at end is nothing to be afraid of",
    "Sub-Phrase With a Small Word in Quotes: 'a Trick, Perhaps?'",
    'sub-phrase with a small word in quotes: "a trick, perhaps?"',
    "Starting a Hyphen Delimited Sub-Phrase With a Small Word - a Trick, Perhaps?",
    "Hyphen Delimited Sub-Phrase With a Small Word in Quotes - 'a Trick, Perhaps?'",
    'Hyphen Delimited sub-phrase with a small word in quotes - "a trick, perhaps?"',
    "Snakes on a Plane - The TV Edit - The Famous Line",
    "Starting an Em Dash Delimited Sub-Phrase With a Small Word — a Trick, Perhaps?",
    "Em Dash Delimited Sub-Phrase With a Small Word in Quotes — 'a Trick, Perhaps?'",
    'Em Dash Delimited sub-phrase with a small word in quotes — "a trick, perhaps?"',
    "Snakes on a Plane — The TV Edit — The Famous Line",
    "EPISODE 7 — THE FORCE AWAKENS",
    "episode 7 – The force awakens",
    "THE CASE OF X ≤ 7",
    "the case of X ≤ 7",
    '"Nothing to Be Afraid of?"',
    '"Nothing to be Afraid Of?"',
    "2lmc Spool: 'gruber on OmniFocus and vapo(u)rware'",
    "this is something listed on del.icio.us",
    "iTunes should be unmolested",
    "reading between the lines of steve jobs’s ‘thoughts on music’",
    "seriously, ‘repair permissions’ is voodoo",
    "generalissimo francisco franco: still dead; kieren McCarthy: still a jackass",
    "O'Reilly should be untouched",
    "my name is o'reilly",
    "Mr McTavish went to MacDonalds",
    "this is http://foo.com",
    "mac mc MAC MC machine",
    "FOO BAR 5TH ST",
    "foo bar 5th st",
    "l'grange l'grange l'Grange l'Grange",
    "L'grange L'grange L'Grange L'Grange",
    "l'GranGe",
    "o'grange O'grange o'Grange O'Grange",
    "o'grange's O'grange's o'Grange's O'Grange's",
    "O'GranGe",
    "o'melveny/o'doyle o'Melveny/o'doyle O'melveny/o'doyle o'melveny/o'Doyle o'melveny/O'doyle",
    "mccay-mcbut-mcdo mcdonalds/mcby",
    "oblon, spivak, mcclelland, maier & neustadt",
    "Mcoblon, spivak, mcclelland, mcmaier, & mcneustadt",
    "mcfoo-bar, MCFOO-BAR, McFoo-bar, McFoo-Bar, mcfoo-mcbar, foo-mcbar",
    "'QUOTE' A GREAT",
    "‘QUOTE’ A GREAT",
    "“YOUNG AND RESTLESS”",
    "EL NIÑO A ARRIVÉ HIER",
    "YEA NO",
    "ÝÆ ÑØ",
    "yea no",
    "ýæ ñø",
    "Mr mr Mrs Ms Mss Dr dr , Mr. and Mrs. Person",
    "a mix\u00a0of\tdifferent\u200aspace\u2006characters",
    "sending UDP packets over PPPoE works great",
    "SENDING UDP PACKETS OVER PPPOE WORKS GREAT",
    "playing the game \"words with friends\"",
    "Line number one",
    "and Line three",
]

SMALL = [
    "a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in",
    "of", "on", "or", "the", "to", "v", "v.", "via", "vs", "vs.",
]
NOUNS = [
    "apple", "bridge", "sea", "music", "technology", "plane", "problem",
    "string", "title", "wrapper", "smith", "jobs", "washington", "example",
    "permissions", "force", "episode", "probe", "deal", "harbor", "night",
    "river", "market", "garden", "letter", "report", "signal", "packet",
    "window", "castle", "orange", "violin", "camera", "bridge", "forest",
]
NAMES = [
    "mcdonald", "mccarthy", "mcintyre", "mcleod", "o'grange", "o'reilly",
    "o'melveny", "l'grange", "d'angelo", "o'doyle", "smith", "jobs", "franco",
]
HONORIFICS = ["mr", "mrs", "ms", "dr", "Mr", "MRS", "Ms", "DR"]
ACRONYMS = ["cnn", "html", "gps", "nfl", "bbc", "ibm", "sec", "udp", "tcp", "rss"]
HOSTS = ["example.com", "del.icio.us", "foo.com", "news.bbc.co.uk", "a.b"]
INTERNAL = ["iTunes", "AT&T", "MacDonalds", "PPPoE", "OmniFocus", "PhD", "IPv6"]
ORDINALS = ["1st", "2nd", "3rd", "4th", "5th", "34th"]
BREAKS = [": ", "; ", ". ", "? ", "! ", " - ", " – ", " — ", " ‒ ", " ― "]
QUOTES = ["'", '"', "‘", "’", "“", "”"]
SPACES = [" ", "  ", "\t", "\u00a0", "\u200a", "\u2006"]


def _ok(text: str) -> bool:
    return bool(text) and not any(ch in LINE_BREAKS for ch in text)


def _word(rng: random.Random) -> str:
    kind = rng.randrange(14)
    if kind == 0:
        return rng.choice(SMALL)
    if kind == 1:
        return rng.choice(NOUNS)
    if kind == 2:
        return rng.choice(NAMES)
    if kind == 3:
        stem = rng.choice(["donald", "tavish", "clelland", "neustadt", "foo", "bar", "kay"])
        return rng.choice(["mc", "Mc", "MC"]) + stem
    if kind == 4:
        return rng.choice(HONORIFICS)
    if kind == 5:
        return rng.choice(ACRONYMS)
    if kind == 6:
        return rng.choice(HOSTS)
    if kind == 7:
        return rng.choice(INTERNAL)
    if kind == 8:
        return rng.choice(ORDINALS)
    if kind == 9:
        letter = rng.choice("ABCDEFGHJKLMNPQRSTUVWXYZ")
        return letter + "."
    if kind == 10:
        left = rng.choice(["d", "o", "l", "D", "O", "L"])
        mark = rng.choice(["'", "‘"])
        rest = rng.choice(["grange", "reilly", "angelo", "melveny", "grange's"])
        return left + mark + rest
    if kind == 11:
        return rng.choice(NOUNS) + "/" + rng.choice(["or", "and", "word", "mcby", "four"])
    if kind == 12:
        return "-".join(rng.choice(SMALL + NOUNS) for _ in range(rng.randint(2, 3)))
    base = rng.choice(NOUNS)
    return rng.choice([base.upper(), base.capitalize(), base])


def _phrase(rng: random.Random, n: int) -> str:
    parts = [_word(rng) for _ in range(n)]
    gap = rng.choice(SPACES)
    return gap.join(parts)


def _random_title(rng: random.Random) -> str:
    style = rng.randrange(8)
    if style == 0:
        text = _phrase(rng, rng.randint(2, 8))
    elif style == 1:
        text = _phrase(rng, rng.randint(3, 7)).upper()
    elif style == 2:
        words = [_word(rng) for _ in range(rng.randint(3, 7))]
        words[-1] = words[-1].upper()
        text = " ".join(words)
    elif style == 3:
        left = _phrase(rng, rng.randint(2, 5))
        right = _phrase(rng, rng.randint(2, 5))
        text = left + rng.choice(BREAKS) + right
    elif style == 4:
        text = "http://" + rng.choice(HOSTS) + " " + _phrase(rng, rng.randint(2, 4))
    elif style == 5:
        quote = rng.choice(QUOTES)
        text = quote + _phrase(rng, rng.randint(2, 6)) + quote
    elif style == 6:
        text = rng.choice(SMALL) + " " + _phrase(rng, rng.randint(2, 5))
    else:
        text = _phrase(rng, rng.randint(2, 5)) + " " + rng.choice(SMALL)
    if rng.randrange(5) == 0:
        text = rng.choice(QUOTES) + text
    return text


def _collect(rng: random.Random) -> list[str]:
    seen: set[str] = set()
    titles: list[str] = []

    def push(text: str) -> None:
        if text in seen or not _ok(text):
            return
        result = titlecase(text)
        if not isinstance(result, str) or not _ok(result):
            return
        seen.add(text)
        titles.append(text)

    for item in CANONICAL:
        push(item)

    while len(titles) < COUNT * 2:
        push(_random_title(rng))

    rng.shuffle(titles)
    return titles


def _write(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    rng = random.Random(1)
    titles = _collect(rng)
    visible = titles[:COUNT]
    hidden = titles[COUNT:COUNT * 2]
    if len(visible) != COUNT or len(hidden) != COUNT:
        raise SystemExit(f"expected {COUNT} lines in each set")
    if set(visible) & set(hidden):
        raise SystemExit("visible and hidden inputs overlap")

    _write(DATA / "inputs.txt", visible)
    _write(DATA / "hidden_inputs.txt", hidden)
    _write(DATA / "expected.txt", [titlecase(line) for line in visible])
    _write(DATA / "hidden_expected.txt", [titlecase(line) for line in hidden])


if __name__ == "__main__":
    main()
