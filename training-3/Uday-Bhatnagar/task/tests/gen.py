#!/usr/bin/env python3
"""Generate the visible and hidden titlecase datasets.

Every expected answer is produced by executing the original
``python-titlecase`` implementation that ships with this assignment.  Nothing
in this file reimplements the titlecase algorithm.

The generator is intentionally deterministic: it calls ``random.seed(1)`` and
never uses time, environment, filesystem ordering, or hash-randomised data.
Run it from anywhere; paths are resolved relative to this file.

Usage:
    python gen.py            # regenerate tests/data/*.txt
    python gen.py --check    # regenerate and verify existing files match
"""

from __future__ import annotations

import argparse
import hashlib
import random
import sys
from pathlib import Path
from typing import Callable

TESTS_DIR = Path(__file__).resolve().parent
TASK_DIR = TESTS_DIR.parent
ORIGINAL_REPO = TASK_DIR.parent / "python-titlecase"
DATA_DIR = TESTS_DIR / "data"

if not (ORIGINAL_REPO / "titlecase" / "__init__.py").is_file():
    raise SystemExit(f"original python-titlecase repository not found at {ORIGINAL_REPO}")

sys.path.insert(0, str(ORIGINAL_REPO))
import titlecase as titlecase_module  # noqa: E402
from titlecase import titlecase  # noqa: E402

if titlecase_module.REGEX_AVAILABLE:
    raise SystemExit(
        "the optional 'regex' package is installed; expected outputs would not "
        "match the authoritative standard-library 're' fallback"
    )

VISIBLE_COUNT = 2000
HIDDEN_COUNT = 2000

# Category -> number of cases in EACH dataset.  The values sum to 2000.
QUOTAS: dict[str, int] = {
    "special_cases": 80,
    "normal_english": 220,
    "small_word_positions": 150,
    "all_uppercase": 150,
    "acronyms": 120,
    "urls": 100,
    "punctuation": 120,
    "apostrophes": 100,
    "hyphenated": 120,
    "slash_separated": 100,
    "initials": 80,
    "abbreviations": 80,
    "mixed_case": 100,
    "unicode": 120,
    "unicode_whitespace": 60,
    "leading_trailing_whitespace": 80,
    "multiple_spaces": 80,
    "ordering_edge_cases": 80,
    "all_rules": 60,
}

assert sum(QUOTAS.values()) == VISIBLE_COUNT == HIDDEN_COUNT

# Characters that would break the one-title-per-physical-line contract.
FORBIDDEN = {
    "\n",
    "\r",
    "\x00",
    "\x0b",
    "\x0c",
    "\x1c",
    "\x1d",
    "\x1e",
    "\x85",
    "\u2028",
    "\u2029",
}

NOUNS = [
    "river", "garden", "library", "mountain", "city", "ocean", "forest",
    "village", "castle", "island", "desert", "valley", "bridge", "market",
    "station", "museum", "theater", "harbor", "meadow", "canyon", "glacier",
    "peninsula", "archipelago", "observatory", "university", "hospital",
    "airport", "cathedral", "fortress", "lighthouse", "workshop", "kitchen",
    "orchard", "factory", "planetarium", "greenhouse", "courtyard", "quarry",
]
ADJECTIVES = [
    "hidden", "silent", "ancient", "modern", "quiet", "bright", "broken",
    "distant", "golden", "lonely", "secret", "wild", "gentle", "frozen",
    "burning", "forgotten", "narrow", "endless", "curious", "patient",
    "restless", "shallow", "towering", "winding", "sunlit", "dusty",
]
VERBS = [
    "discover", "build", "explore", "remember", "imagine", "protect",
    "restore", "describe", "question", "follow", "design", "understand",
    "measure", "celebrate", "challenge", "inspect", "repair", "record",
]
PLACES = [
    "the north", "the coast", "the mountains", "the city", "the desert",
    "the valley", "the border", "the islands", "the countryside",
    "the capital", "the frontier", "the river", "the forest", "the harbor",
    "the plains", "the highlands", "the wetlands", "the old town",
]
NAMES = [
    "Alice", "Marco", "Elena", "Tomas", "Priya", "Jonah", "Maya", "Oscar",
    "Nadia", "Felix", "Ingrid", "Rafael", "Yuki", "Amara", "Leo", "Sofia",
    "Hugo", "Iris", "Dmitri", "Leila", "Nora", "Samir", "Clara", "Mateo",
]
TOPICS = [
    "memory", "language", "weather", "migration", "architecture", "music",
    "science", "history", "travel", "cooking", "gardening", "astronomy",
    "geology", "poetry", "economics", "medicine", "education", "transport",
    "photography", "cartography", "oceanography", "linguistics",
]
AUDIENCES = [
    "beginners", "students", "travelers", "families", "engineers", "teachers",
    "writers", "artists", "researchers", "children", "pilots", "chefs",
    "musicians", "historians", "doctors", "volunteers", "commuters",
]
SMALL_WORDS = [
    "a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in",
    "of", "on", "or", "the", "to", "v", "v.", "via", "vs", "vs.",
]
ACRONYMS = [
    "CNN", "BBC", "NFC", "NSA", "TCP", "UDP", "PHP", "SQL", "NASA", "ESA",
    "FBI", "CIA", "NATO", "HTML", "CSS", "JSON", "XML", "AWS", "GPU", "CPU",
    "RAM", "SSD", "VPN", "DNS", "HTTP", "FTP", "API", "SDK", "MIT", "NPR",
]
CONSONANT_WORDS = [
    "cnn", "nbc", "tcp", "dns", "vpn", "gpu", "sdk", "xml", "css", "php",
    "sql", "hrs", "mtn", "brd", "cst", "fnd", "lck", "prk", "str", "nfl",
]
DOMAINS = [
    "example.com", "example.org", "python.org", "golang.org", "github.com",
    "wikipedia.org", "archive.org", "nytimes.com", "bbc.co.uk", "nasa.gov",
    "mit.edu", "openstreetmap.org", "wikimedia.org", "ietf.org",
]
PATHS = [
    "docs", "docs/getting-started", "reference/api", "downloads/stable",
    "blog/2024/notes", "projects/titlecase", "wiki/Main_Page", "a/b/c",
]
SCHEMES = ["http", "https", "ftp"]
HYPHENATED = [
    "state-of-the-art", "well-known", "self-contained", "up-to-date",
    "mother-in-law", "twenty-one", "e-mail", "X-ray", "T-shirt", "long-term",
    "high-quality", "low-budget", "part-time", "full-stack", "open-source",
    "real-world", "end-to-end", "two-not-three", "five-and", "three-by-four",
    "read-only", "world-class", "cost-effective", "user-friendly",
]
SLASHED = [
    "and/or", "path/to/file", "word/word", "client/server", "read/write",
    "TCP/IP", "n/a", "input/output", "yes/no", "pro/con", "either/or",
    "this/that", "me/you", "fast/slow", "black/white", "http://x/y",
    "//server/share", "C:/Users/foo", "docs/api/v2", "parent/child",
]
INITIALS = [
    "U.S.A.", "D.C.", "J.R.R.", "A.B.", "E.T.", "U.K.", "U.N.", "M.I.T.",
    "F.B.I.", "C.I.A.", "A.I.", "B.B.C.", "N.Y.", "L.A.", "R.E.M.",
]
MIXED_CASE = [
    "iTunes", "iPhone", "iPad", "macOS", "eBay", "YouTube", "JavaScript",
    "TypeScript", "GitHub", "LinkedIn", "McDonald", "McTavish", "camelCase",
    "PascalCase", "PPPoE", "AT&T", "Q&A", "2lmc", "OmniFocus", "vapo(u)rware",
    "del.icio.us", "example.com", "UDP", "SQLite", "GraphQL", "devOps",
]
UNICODE_TITLES = [
    "EL NIÑO A ARRIVÉ HIER", "ÝÆ ÑØ", "ýæ ñø", "straße", "ß", "ﬁle",
    "İstanbul", "ISTANBUL", "naïve café", "Zürich", "São Paulo", "Ελλάδα",
    "Москва", "東京", "café au lait", "piñata", "crème brûlée",
    "smørrebrød", "ΑΘΗΝΑ", "ПРИВЕТ МИР", "Über die Brücke", "façade",
    "jalapeño", "München", "Köln", "Reykjavík", "Ångström", "œuvre",
    "déjà vu", "résumé", "coöperate", "İzmir", "Kraków", "Žižkov",
]
UNICODE_SPACES = ["\u00a0", "\u2002", "\u2003", "\u2009", "\u202f", "\u3000", "\t"]


def pick(rng: random.Random, values: list[str] | tuple[str, ...]) -> str:
    return values[rng.randrange(len(values))]


def title(rng: random.Random) -> str:
    """A realistic mixed-case English title fragment."""
    adj = pick(rng, ADJECTIVES)
    noun = pick(rng, NOUNS)
    noun2 = pick(rng, NOUNS)
    place = pick(rng, PLACES)
    form = rng.randrange(8)
    if form == 0:
        return f"the {adj} {noun} of {place}"
    if form == 1:
        return f"{adj} {noun} and the {noun2}"
    if form == 2:
        return f"a {adj} {noun} in {place}"
    if form == 3:
        return f"{pick(rng, NAMES)} and the {adj} {noun}"
    if form == 4:
        return f"why the {noun} matters in {place}"
    if form == 5:
        return f"the {noun} that {pick(rng, VERBS)} {place}"
    if form == 6:
        return f"how to {pick(rng, VERBS)} a {noun}"
    return f"notes on {pick(rng, TOPICS)} and the {adj} {noun}"


def cat_special_cases(rng: random.Random) -> str:
    fixed = [
        "  a thing", "\ta thing", "afraid of  ", " a ", "a  thing",
        "and/or", "and/or test", "test and/or", "x and/or y", "five-and",
        "three-by-four", "Mc", "MC", "Mss", "AT&T", "q&a", "u.s.a.",
        "http://x/y", "//server/share", "of  ",
        "Small word at end is nothing to be afraid of", "the lord of the rings",
        "this v. that", "this vs that", "this vs. that",
        "a title and/or string", "path/to/file", "C:/Users/foo", "FOO-BAR",
        "THIS IS A TEST", "MCDONALDS", "mcdonalds", "MR MRS MS DR", "MR.",
        "Dr.", "34th 3rd 2nd", "5th", "foo_bar", "_foo", "-word", "/word",
        "U.S.A. foo", "http://foo.com", "iTunes should be unmolested",
        "'QUOTE' A GREAT", "‘QUOTE’ A GREAT", "“YOUNG AND RESTLESS”",
        "FOO BAR 5TH ST", "Words with all consonants like cnn are acronyms",
        "Mr McTavish went to MacDonalds",
        "Mr mr Mrs Ms Mss Dr dr , Mr. and Mrs. Person",
        "dance with me/let’s face the music and dance",
        "sending UDP packets over PPPoE works great",
        "2lmc Spool: 'gruber on OmniFocus and vapo(u)rware'",
        "What is AT&T's problem?",
        "this is just an example.com",
        "this is something listed on del.icio.us",
        "Q&A with steve jobs: 'that's what happens in technology'",
    ]
    # Parameterised variants keep the category large without inventing rules.
    name = pick(rng, NAMES)
    noun = pick(rng, NOUNS)
    noun2 = pick(rng, NOUNS)
    place = pick(rng, PLACES)
    variants = [
        f"  {pick(rng, SMALL_WORDS)} {noun}",
        f"\t{pick(rng, SMALL_WORDS)} {noun}",
        f"{noun} {pick(rng, SMALL_WORDS)}  ",
        f" {pick(rng, SMALL_WORDS)} ",
        f"{noun}  {noun2}",
        f"{name}/or/{pick(rng, NAMES)}",
        f"{noun}-and-{noun2}",
        f"Mr. and Mrs. {name}",
        f"Dr. {name} and the {noun}",
        f"u.s.a. {noun}",
        f"U.S.A. {noun}",
        f"{noun} v. {noun2}",
        f"{noun} vs. {noun2}",
        f"the {noun} of {place}",
        f"'{noun}' A {noun2}",
        f"‘{noun}’ {pick(rng, NAMES)}",
        f"“{noun}” AND {noun2}",
        f"{name}’s ‘{noun}’",
        f"{noun}: a {noun2}",
        f"{noun}; {pick(rng, SMALL_WORDS)} {noun2}",
    ]
    return pick(rng, fixed + variants)


def cat_normal_english(rng: random.Random) -> str:
    adj = pick(rng, ADJECTIVES)
    noun = pick(rng, NOUNS)
    noun2 = pick(rng, NOUNS)
    name = pick(rng, NAMES)
    name2 = pick(rng, NAMES)
    place = pick(rng, PLACES)
    topic = pick(rng, TOPICS)
    topic2 = pick(rng, TOPICS)
    audience = pick(rng, AUDIENCES)
    verb = pick(rng, VERBS)
    form = rng.randrange(14)
    if form == 0:
        return f"the {noun} of the {noun2}"
    if form == 1:
        return f"{name} and the {adj} {noun}"
    if form == 2:
        return f"a {adj} {noun} in {place}"
    if form == 3:
        return f"why {topic} matters in {place}"
    if form == 4:
        return f"the {adj} {noun} that {verb} {place}"
    if form == 5:
        return f"how to {verb} a {noun}"
    if form == 6:
        return f"{adj} {noun} for {audience}"
    if form == 7:
        return f"notes on {topic}"
    if form == 8:
        return f"the {noun} of {name}"
    if form == 9:
        return f"on {topic} and {topic2}"
    if form == 10:
        return f"{name}'s {adj} {noun}"
    if form == 11:
        return f"{name} meets {name2} at the {noun}"
    if form == 12:
        return f"a short history of {topic}"
    return f"the {noun} and the {adj} {noun2}"


def cat_small_word_positions(rng: random.Random) -> str:
    s1 = pick(rng, SMALL_WORDS)
    s2 = pick(rng, SMALL_WORDS)
    s3 = pick(rng, SMALL_WORDS)
    noun = pick(rng, NOUNS)
    noun2 = pick(rng, NOUNS)
    noun3 = pick(rng, NOUNS)
    place = pick(rng, PLACES)
    form = rng.randrange(10)
    if form == 0:
        return f"{s1} {noun}"
    if form == 1:
        return f"{noun} {s1} {noun2}"
    if form == 2:
        return f"{noun} {s1} {noun2} {s2} {noun3}"
    if form == 3:
        return f"{s1} {noun} {s2} {noun2} {s3}"
    if form == 4:
        return f"{noun} {s1}"
    if form == 5:
        return f"{s1} {noun} {s2}"
    if form == 6:
        return f"{noun}, {s1} {noun2}"
    if form == 7:
        return f"{noun}: {s1} {noun2}"
    if form == 8:
        return f"{noun} {s1} {noun2}, {s2} {noun3}"
    return f"the {noun} in {place} {s1} {noun2}"


def cat_all_uppercase(rng: random.Random) -> str:
    noun = pick(rng, NOUNS)
    noun2 = pick(rng, NOUNS)
    noun3 = pick(rng, NOUNS)
    adj = pick(rng, ADJECTIVES)
    name = pick(rng, NAMES)
    verb = pick(rng, VERBS)
    place = pick(rng, PLACES)
    small = pick(rng, SMALL_WORDS)
    form = rng.randrange(10)
    if form == 0:
        return f"{noun} {noun2} {noun3}".upper()
    if form == 1:
        return f"{name} {verb} THE {noun} IN {place}".upper()
    if form == 2:
        return f"{adj} {noun} AND {adj.upper()} {noun2}"
    if form == 3:
        return f"{name} SAID THE {noun} WAS {adj.upper()}"
    if form == 4:
        return f"EPISODE {rng.randrange(2, 30)} — THE {noun} {verb}".upper()
    if form == 5:
        return f"{noun} {noun2} {small} {noun3}".upper()
    if form == 6:
        return f"THE {noun} OF THE {noun2}".upper()
    if form == 7:
        return f"{adj} {noun} ({noun2})".upper()
    if form == 8:
        return f"{place} {verb} {noun}".upper()
    return f"{name} AND {pick(rng, NAMES)} VISIT {place}".upper()


def cat_acronyms(rng: random.Random) -> str:
    acr = pick(rng, ACRONYMS)
    acr2 = pick(rng, ACRONYMS)
    acr3 = pick(rng, ACRONYMS)
    cons = pick(rng, CONSONANT_WORDS)
    cons2 = pick(rng, CONSONANT_WORDS)
    noun = pick(rng, NOUNS)
    name = pick(rng, NAMES)
    form = rng.randrange(11)
    if form == 0:
        return f"{acr} and {acr2} report on the {noun}"
    if form == 1:
        return f"the {acr} uses {acr2} and {acr3}"
    if form == 2:
        return f"{acr} is not the same as {acr.lower()}"
    if form == 3:
        return f"{cons} is short"
    if form == 4:
        return f"the {cons2} network"
    if form == 5:
        return f"{name} works at {acr}"
    if form == 6:
        return f"{acr} {acr2} {noun}".upper()
    if form == 7:
        return f"AT&T and Q&A"
    if form == 8:
        return f"the {acr} team met the {acr2} team"
    if form == 9:
        return f"{cons} and {cons2} are acronyms"
    return f"{acr} {acr2} and {acr3}"


def cat_urls(rng: random.Random) -> str:
    domain = pick(rng, DOMAINS)
    domain2 = pick(rng, DOMAINS)
    path = pick(rng, PATHS)
    path2 = pick(rng, PATHS)
    scheme = pick(rng, SCHEMES)
    noun = pick(rng, NOUNS)
    name = pick(rng, NAMES).lower()
    form = rng.randrange(11)
    if form == 0:
        return f"visit https://{domain} for details"
    if form == 1:
        return f"{scheme}://{domain}/{path} is the official site"
    if form == 2:
        return f"read more at https://{domain}/{path}"
    if form == 3:
        return f"the docs live at {scheme}://{domain}/{path2}"
    if form == 4:
        return f"https://{domain} and https://{domain2}"
    if form == 5:
        return f"download from {scheme}://{domain}/downloads/{noun}"
    if form == 6:
        return f"https://{domain}/{path}?q={noun}&lang=en"
    if form == 7:
        return f"https://{domain}/{path}#{noun}"
    if form == 8:
        return f"{name}@{domain} wrote about {noun}"
    if form == 9:
        return f"//server/share/{noun}"
    return f"http://x/y and https://{domain}"


def cat_punctuation(rng: random.Random) -> str:
    base = title(rng)
    noun = pick(rng, NOUNS)
    noun2 = pick(rng, NOUNS)
    name = pick(rng, NAMES)
    small = pick(rng, SMALL_WORDS)
    form = rng.randrange(14)
    if form == 0:
        return f"'{base}'"
    if form == 1:
        return f"“{base}”"
    if form == 2:
        return f"‘{base}’"
    if form == 3:
        return f"{base}!"
    if form == 4:
        return f"{base}?"
    if form == 5:
        return f"({base})"
    if form == 6:
        return f"[{base}]"
    if form == 7:
        return f"— {base}"
    if form == 8:
        return f"…{base}"
    if form == 9:
        return f"{base}: {small} {noun}"
    if form == 10:
        return f"{name}. {small} {noun}"
    if form == 11:
        return f"{base}; {small} {noun}"
    if form == 12:
        return f"{base} — {small} {noun2}"
    return f"{base} - {small} {noun2}"


def cat_apostrophes(rng: random.Random) -> str:
    apos = [
        "o'reilly", "d'angelo", "l'grange", "o'neill", "d'artagnan",
        "l'oreal", "o'connor", "d'urso", "l'amour", "o'malley",
    ]
    fixed = [
        "my name is o'reilly",
        "O'Reilly should be untouched",
        "l'grange l'grange l'Grange l'Grange",
        "o'grange's O'grange's o'Grange's O'Grange's",
        "reading between the lines of steve jobs’s ‘thoughts on music’",
        "it's a wonderful life",
        "don't stop believing",
        "the cat's pajamas",
        "rock 'n' roll",
        "O'NEILL AND D'ANGELO",
        "l'GranGe",
        "d'ANGELO",
    ]
    word = pick(rng, apos)
    noun = pick(rng, NOUNS)
    name = pick(rng, NAMES)
    verb = pick(rng, VERBS)
    form = rng.randrange(7)
    if form == 0:
        return f"{word} {verb} the {noun}"
    if form == 1:
        return f"{name} met {word} near the {noun}"
    if form == 2:
        return f"{word}'s {noun} is here"
    if form == 3:
        return f"{word} and {pick(rng, apos)}"
    if form == 4:
        return f"the {noun} of {word}"
    if form == 5:
        return f"{word.upper()} {noun}".upper()
    return f"{name}'s {noun} and {word}"


def cat_hyphenated(rng: random.Random) -> str:
    hy = pick(rng, HYPHENATED)
    hy2 = pick(rng, HYPHENATED)
    noun = pick(rng, NOUNS)
    audience = pick(rng, AUDIENCES)
    form = rng.randrange(7)
    if form == 0:
        return f"{hy} {noun}"
    if form == 1:
        return f"a {hy} {noun} for {audience}"
    if form == 2:
        return f"{hy} and {hy2}"
    if form == 3:
        return f"{hy}/{hy2}"
    if form == 4:
        return f"{hy} {hy2} {noun}"
    if form == 5:
        return f"the {hy} {noun} in the {hy2} district"
    return f"{hy.upper()} {noun}"


def cat_slash_separated(rng: random.Random) -> str:
    sl = pick(rng, SLASHED)
    sl2 = pick(rng, SLASHED)
    noun = pick(rng, NOUNS)
    noun2 = pick(rng, NOUNS)
    small = pick(rng, SMALL_WORDS)
    form = rng.randrange(8)
    if form == 0:
        return f"{sl} {noun}"
    if form == 1:
        return f"a {noun} and/or {noun}"
    if form == 2:
        return f"{sl} {sl2}"
    if form == 3:
        return f"the {sl} rule"
    if form == 4:
        return f"{noun}/{sl}"
    if form == 5:
        return f"{noun}/{sl}/{noun2}"
    if form == 6:
        return f"path/to/{noun}/file"
    return f"{noun} {sl} {noun}"


def cat_initials(rng: random.Random) -> str:
    ini = pick(rng, INITIALS)
    ini2 = pick(rng, INITIALS)
    name = pick(rng, NAMES)
    noun = pick(rng, NOUNS)
    place = pick(rng, PLACES)
    form = rng.randrange(9)
    if form == 0:
        return f"{ini} is here"
    if form == 1:
        return f"the {ini} office"
    if form == 2:
        return f"{name} {ini} {pick(rng, NAMES)}"
    if form == 3:
        return f"{ini} SHOULD BE FIXED BUT MIGHT BE A PROBLEM"
    if form == 4:
        return f"WASHINGTON, {ini} AND THE {noun}"
    if form == 5:
        return f"{ini} and {ini2}"
    if form == 6:
        return f"e.g. the {noun}"
    if form == 7:
        return f"{name} earned a Ph.D. in {pick(rng, TOPICS)}"
    return f"i.e. {place}"


def cat_abbreviations(rng: random.Random) -> str:
    noun = pick(rng, NOUNS)
    place = pick(rng, PLACES)
    name = pick(rng, NAMES)
    fixed = [
        "mr smith", "mrs jones", "ms adams", "dr brown",
        "MR HARRIS", "MRS LEE", "MS KIM", "DR PATEL",
        "Mr. Smith", "Mrs. Jones", "Ms. Adams", "Dr. Brown",
        "Mss Smith", "St. Louis", "vs. the other", "v. the state",
        "etc. and so on", "approx. five miles", "No. 5",
    ]
    form = rng.randrange(8)
    if form == 0:
        return pick(rng, fixed)
    if form == 1:
        return f"{pick(rng, ['mr', 'mrs', 'ms', 'dr', 'MR', 'MRS', 'MS', 'DR'])} {name}"
    if form == 2:
        return f"{pick(rng, ['Mr.', 'Mrs.', 'Ms.', 'Dr.'])} {name} visited {place}"
    if form == 3:
        return f"{name} and Dr. {pick(rng, NAMES)}"
    if form == 4:
        return f"St. {name} and the {noun}"
    if form == 5:
        return f"{noun} vs. {noun}"
    if form == 6:
        return f"approx. {rng.randrange(2, 20)} miles from {place}"
    return f"Mss {name} met Dr. {pick(rng, NAMES)}"


def cat_mixed_case(rng: random.Random) -> str:
    mixed = pick(rng, MIXED_CASE)
    mixed2 = pick(rng, MIXED_CASE)
    noun = pick(rng, NOUNS)
    fixed = [
        "iTunes should be unmolested",
        "sending UDP packets over PPPoE works great",
        "2lmc Spool: 'gruber on OmniFocus and vapo(u)rware'",
        "What is AT&T's problem?",
        "McDonald's and McTavish",
    ]
    form = rng.randrange(7)
    if form == 0:
        return f"{mixed} is a {noun}"
    if form == 1:
        return f"{mixed} and {mixed2}"
    if form == 2:
        return f"the {mixed} {noun}"
    if form == 3:
        return f"{noun} for {mixed} users"
    if form == 4:
        return f"{mixed} {mixed2} {noun}"
    if form == 5:
        return pick(rng, fixed)
    return f"{mixed} in the {noun}"


def cat_unicode(rng: random.Random) -> str:
    text = pick(rng, UNICODE_TITLES)
    name = pick(rng, ["Zoë", "Renée", "Søren", "Björk", "Aïcha", "Noël", "João", "Māris"])
    noun = pick(rng, ["café", "château", "façade", "résumé", "crêpe", "ménage"])
    form = rng.randrange(5)
    if form == 0:
        return text
    if form == 1:
        return f"{text} and {pick(rng, UNICODE_TITLES)}"
    if form == 2:
        return f"{name} visited the {noun}"
    if form == 3:
        return f"the {noun} of {name}"
    return f"{text}: {pick(rng, UNICODE_TITLES)}"


def cat_unicode_whitespace(rng: random.Random) -> str:
    ws = pick(rng, UNICODE_SPACES)
    ws2 = pick(rng, UNICODE_SPACES)
    noun = pick(rng, NOUNS)
    noun2 = pick(rng, NOUNS)
    small = pick(rng, SMALL_WORDS)
    form = rng.randrange(6)
    if form == 0:
        return f"the{ws}lord{ws}of{ws}the{ws}rings"
    if form == 1:
        return f"a{ws}tale{ws}of{ws}two{ws}cities"
    if form == 2:
        return f"{ws}{noun}{ws}{noun2}{ws}"
    if form == 3:
        return f"text{ws}with{ws}whitespace"
    if form == 4:
        return f"{noun}{ws}{small}{ws}{noun2}"
    return f"{noun}{ws}{ws2}{noun2}"


def cat_leading_trailing_whitespace(rng: random.Random) -> str:
    pad = pick(rng, ["  ", "\t", "   ", "\t\t", " \t", "\t "])
    pad2 = pick(rng, ["  ", "\t", "   ", "\t\t", " \t", "\t "])
    noun = pick(rng, NOUNS)
    noun2 = pick(rng, NOUNS)
    small = pick(rng, SMALL_WORDS)
    form = rng.randrange(6)
    if form == 0:
        return f"{pad}{noun} {small} {noun2}"
    if form == 1:
        return f"{noun} {small} {noun2}{pad}"
    if form == 2:
        return f"{pad}{noun} {small} {noun2}{pad2}"
    if form == 3:
        return f"{pad}{pick(rng, SMALL_WORDS)} {noun}"
    if form == 4:
        return f"{noun} {pick(rng, SMALL_WORDS)}{pad}"
    return f"{pad}{noun}{pad2}"


def cat_multiple_spaces(rng: random.Random) -> str:
    n = rng.randrange(2, 6)
    gap = " " * n
    noun = pick(rng, NOUNS)
    noun2 = pick(rng, NOUNS)
    small = pick(rng, SMALL_WORDS)
    form = rng.randrange(6)
    if form == 0:
        return f"{noun}{gap}{noun2}"
    if form == 1:
        return f"a mix{gap}of{gap}{pick(rng, ADJECTIVES)}{gap}{noun}"
    if form == 2:
        return f"{gap}{noun} {small} {noun2}"
    if form == 3:
        return f"{noun} {small} {noun2}{gap}"
    if form == 4:
        return f"space{gap}between{gap}every{gap}word"
    return f"{noun}{gap}{small}{gap}{noun2}{gap}{pick(rng, ADJECTIVES)}"


def cat_ordering_edge_cases(rng: random.Random) -> str:
    noun = pick(rng, NOUNS)
    noun2 = pick(rng, NOUNS)
    name = pick(rng, NAMES)
    base = title(rng)
    fixed = [
        "u.s.a.",
        "Mr. and Mrs. Person",
        "'QUOTE' A GREAT",
        "‘QUOTE’ A GREAT",
        "“YOUNG AND RESTLESS”",
        "Q&A with steve jobs: 'that's what happens in technology'",
        "a-b end-to-end two-not-three/three-by-four/five-and",
        "MCDONALDS",
        "mcdonalds",
        "mccay-mcbut-mcdo mcdonalds/mcby",
        "O'Reilly should be untouched",
        "l'grange l'grange l'Grange l'Grange",
        "o'grange's O'grange's o'Grange's O'Grange's",
        "WASHINGTON, D.C. SHOULD BE FIXED BUT MIGHT BE A PROBLEM",
        "MR MRS MS DR",
        "AT&T",
        "THIS IS A TEST",
        "EPISODE 7 — THE FORCE AWAKENS",
        "afraid of  ",
        "  a thing",
        " a ",
        "and/or",
        "test and/or",
        "x and/or y",
        "five-and",
        "three-by-four",
        "O'NEILL-FITZGERALD/BYRNES",
        "MCDONALD'S-HOUSE",
        "THE HTTP://X/Y TEST",
        "Dr. Smith and the CNN team: a state-of-the-art TCP/IP system",
    ]
    variants = [
        f"Mr. and Mrs. {name}",
        f"the {noun}: a {noun2}",
        f"u.s.a. {noun}",
        f"U.S.A. {noun}",
        f"{name}’s ‘{noun}’",
        f"— {base}",
        f"{base}: a {noun}",
        f"{base}. {pick(rng, SMALL_WORDS)} {noun2}",
        f"{pick(rng, SMALL_WORDS)} {noun}: {pick(rng, SMALL_WORDS)} {noun2}",
        f"{noun.upper()} and {noun2.lower()}",
        f"{pick(rng, HYPHENATED)}/{pick(rng, HYPHENATED)}",
        f"{pick(rng, ACRONYMS)}'s {pick(rng, HYPHENATED)} {noun}",
    ]
    return pick(rng, fixed + variants)


def cat_all_rules(rng: random.Random) -> str:
    honorific = pick(rng, ["Dr.", "Mr.", "Mrs.", "Ms."])
    name = pick(rng, NAMES)
    acr = pick(rng, ACRONYMS)
    hy = pick(rng, HYPHENATED)
    sl = pick(rng, SLASHED)
    apos = pick(rng, ["o'reilly", "d'angelo", "l'grange"])
    ini = pick(rng, INITIALS)
    noun = pick(rng, NOUNS)
    noun2 = pick(rng, NOUNS)
    small = pick(rng, SMALL_WORDS)
    form = rng.randrange(8)
    if form == 0:
        return (
            f"{honorific} {name} and the {acr} team: a {hy} {noun} for "
            f"{apos}'s {noun2} in the {ini}"
        )
    if form == 1:
        return f"the {acr} report on {hy} {sl} systems: {small} {noun}"
    if form == 2:
        return f"{ini} SHOULD READ THE {hy} {noun} AND THE {acr} NOTES"
    if form == 3:
        return f"{apos} {hy}/{sl} {noun} for {honorific} {name}"
    if form == 4:
        return f"{name}'s {sl} {noun}: {small} {hy} {noun2}"
    if form == 5:
        return f"{acr} and {ini} {hy} {noun} — {small} {noun2}"
    if form == 6:
        return f"{honorific} {name} said: '{apos}' {hy} {noun}"
    return f"the {acr} {sl} {hy} {noun} of {name} and {ini}"


CATEGORIES: dict[str, Callable[[random.Random], str]] = {
    "special_cases": cat_special_cases,
    "normal_english": cat_normal_english,
    "small_word_positions": cat_small_word_positions,
    "all_uppercase": cat_all_uppercase,
    "acronyms": cat_acronyms,
    "urls": cat_urls,
    "punctuation": cat_punctuation,
    "apostrophes": cat_apostrophes,
    "hyphenated": cat_hyphenated,
    "slash_separated": cat_slash_separated,
    "initials": cat_initials,
    "abbreviations": cat_abbreviations,
    "mixed_case": cat_mixed_case,
    "unicode": cat_unicode,
    "unicode_whitespace": cat_unicode_whitespace,
    "leading_trailing_whitespace": cat_leading_trailing_whitespace,
    "multiple_spaces": cat_multiple_spaces,
    "ordering_edge_cases": cat_ordering_edge_cases,
    "all_rules": cat_all_rules,
}


def validate_input(value: str) -> None:
    if not isinstance(value, str):
        raise TypeError(f"input must be str, got {type(value).__name__}")
    if value == "":
        raise ValueError("empty input title")
    if value.strip() == "":
        raise ValueError("whitespace-only input title")
    for char in FORBIDDEN:
        if char in value:
            raise ValueError(f"input contains forbidden character U+{ord(char):04X}: {value!r}")


def expected_for(value: str) -> str:
    output = titlecase(value)
    if "\n" in output or "\r" in output or "\x00" in output:
        raise ValueError(f"expected output contains a forbidden character: {value!r}")
    return output


def generate_dataset(
    rng: random.Random,
    quota: dict[str, int],
    used: set[str],
) -> list[tuple[str, str, str]]:
    records: list[tuple[str, str, str]] = []
    for category, count in quota.items():
        generator = CATEGORIES[category]
        local: set[str] = set()
        attempts = 0
        while len(local) < count:
            attempts += 1
            if attempts > count * 500:
                raise RuntimeError(
                    f"category {category!r} exhausted after {attempts} attempts; "
                    f"generated {len(local)} of {count} unique titles"
                )
            value = generator(rng)
            validate_input(value)
            if value in local or value in used:
                continue
            local.add(value)
            used.add(value)
            records.append((category, value, expected_for(value)))
    return records


def write_records(path: Path, values: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for value in values:
            handle.write(value)
            handle.write("\n")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="regenerate in memory and fail if the on-disk files differ",
    )
    args = parser.parse_args()

    random.seed(1)
    rng = random.Random(1)

    used: set[str] = set()
    visible = generate_dataset(rng, QUOTAS, used)
    hidden = generate_dataset(rng, QUOTAS, used)

    # Dataset order is deterministic but mixed so categories are not grouped.
    rng.shuffle(visible)
    rng.shuffle(hidden)

    if len(visible) != VISIBLE_COUNT or len(hidden) != HIDDEN_COUNT:
        raise RuntimeError("generated record counts do not match the requirement")
    if {r[1] for r in visible} & {r[1] for r in hidden}:
        raise RuntimeError("visible and hidden datasets overlap")

    files = {
        "inputs.txt": [r[1] for r in visible],
        "expected.txt": [r[2] for r in visible],
        "hidden_inputs.txt": [r[1] for r in hidden],
        "hidden_expected.txt": [r[2] for r in hidden],
    }

    if args.check:
        mismatches = []
        for name, values in files.items():
            path = DATA_DIR / name
            if not path.exists():
                mismatches.append(f"missing {path}")
                continue
            expected_text = "".join(value + "\n" for value in values)
            if path.read_text(encoding="utf-8") != expected_text:
                mismatches.append(f"content differs: {path}")
        if mismatches:
            for mismatch in mismatches:
                print(f"FAIL: {mismatch}", file=sys.stderr)
            return 1
        print("OK: generated data matches on-disk files")
        return 0

    for name, values in files.items():
        write_records(DATA_DIR / name, values)

    print(f"visible cases: {len(visible)}")
    print(f"hidden cases:  {len(hidden)}")
    for category, count in QUOTAS.items():
        print(f"  visible {category}: {count}; hidden {category}: {count}")
    print("outputs:")
    for name in files:
        path = DATA_DIR / name
        print(f"  {name}: {path.stat().st_size} bytes sha256={sha256(path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
