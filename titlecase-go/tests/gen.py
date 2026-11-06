#!/usr/bin/env python3
"""Deterministic stdin fixtures for the python-titlecase Go port.

Expected lines are produced by the original ``titlecase()`` function with its
default arguments. Inputs are single titles and never contain CR or LF.
"""

import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "environment" / "python-titlecase"))

from titlecase import titlecase  # noqa: E402

DATA_DIR = Path(__file__).resolve().parent / "data"
COUNT = 2000

SMALL_WORDS = [
    "a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in",
    "of", "on", "or", "the", "to", "v", "v.", "via", "vs", "vs.",
]
CONTENT = [
    "apple", "bridge", "castle", "dragon", "engine", "forest", "garden",
    "harbor", "island", "jungle", "knight", "lantern", "mountain", "notebook",
    "ocean", "piano", "quartz", "river", "shadow", "tower", "umbrella",
    "valley", "window", "yellow", "zebra", "science", "history", "music",
    "market", "voyage", "captain", "signal", "harvest", "library", "compass",
    "meadow", "canyon", "beacon", "orchard", "summit",
]
CAMEL = [
    "fooBar", "iPhone", "iTunes", "macOS", "eBay", "YouTube", "OpenSSL",
    "PPPoE", "OmniFocus", "iPad", "JavaScript", "macOS",
]
DOMAINS = [
    "example.com", "del.icio.us", "nytimes.com", "bbc.co.uk", "U.S.",
    "e.g.", "i.e.", "Ph.D", "washington.edu",
]
ACRONYMS = ["xkcd", "cnn", "html", "css", "ibm", "gps", "sql", "lcd", "bbc", "nbc", "fft", "dhcp"]
HONORIFICS = ["mr", "mrs", "ms", "dr", "MR", "MRS", "MS", "DR", "Mr", "Mrs", "Ms", "Dr"]
MC_WORDS = [
    "mcdonald", "mccarthy", "mcgregor", "mckinley", "mcclelland", "mcfly",
    "mctavish", "mcdonalds", "McDonald", "MCFLY", "mcfoo", "McTavish",
]
INITIALS = ["A.B", "A.B.C", "A.B.C.", "U.S", "N.Y", "D.C", "J.R.R"]
APOS_TAILS = ["reilly", "brien", "malley", "artagnan", "angelo", "amour", "oreal", "grange", "melveny", "doyle"]
HYPHENS = ["mother-in-law", "state-of-the-art", "end-to-end", "well-known", "two-not-three", "editor-in-chief"]
SLASHES = ["foo/bar", "and/or", "read/write", "input/output", "three-by-four", "north/south"]
SUB_MARKS = [":", ";", ".", "?", "!", "-", "–", "‒", "—", "―"]
LEADERS = ["'", '"', "(", "[", "“", "‘", "*"]
UNICODE_WORDS = ["niño", "crème", "brûlée", "café", "naïve", "résumé", "ångström"]


def _ok(line):
    return bool(line) and "\n" not in line and "\r" not in line


def _pick(options):
    return random.choice(options)


def _words(n):
    return [_pick(CONTENT) for _ in range(n)]


def _vary(word):
    style = random.randrange(4)
    if style == 0:
        return word.lower()
    if style == 1:
        return word.upper()
    if style == 2:
        return word.capitalize()
    return word


def _sentence(n=None, vary=False):
    count = n if n is not None else random.randint(2, 8)
    parts = _words(count)
    if vary:
        parts = [_vary(part) for part in parts]
    return parts


def _join(parts):
    return " ".join(parts)


def normal_title():
    return _join(_sentence(vary=True))


def small_middle():
    parts = _sentence(random.randint(4, 7))
    parts[random.randrange(1, len(parts) - 1)] = _pick(SMALL_WORDS)
    if random.random() < 0.5:
        parts[random.randrange(1, len(parts) - 1)] = _pick(SMALL_WORDS)
    return _join(parts)


def small_edges():
    parts = _sentence(random.randint(3, 6))
    parts[0] = _pick(SMALL_WORDS)
    parts[-1] = _pick(SMALL_WORDS)
    return _join(parts)


def apostrophe_title():
    left = _pick("dol")
    mark = _pick(["'", "‘"])
    word = left + mark + _pick(APOS_TAILS)
    if random.random() < 0.3:
        word += "'s"
    parts = _sentence(random.randint(2, 5))
    parts.insert(random.randrange(len(parts) + 1), word)
    return _join(parts)


def mc_title():
    parts = _sentence(random.randint(2, 5))
    parts.insert(random.randrange(len(parts) + 1), _pick(MC_WORDS))
    if random.random() < 0.4:
        parts.append(_pick(["mcfoo-mcbar", "mccay-mcbut-mcdo", "foo-mcbar", "mcdonalds/mcby"]))
    return _join(parts)


def honorific_title():
    parts = _sentence(random.randint(2, 5))
    parts.insert(0, _pick(HONORIFICS))
    if random.random() < 0.5:
        parts.insert(random.randrange(1, len(parts) + 1), _pick(HONORIFICS))
    return _join(parts)


def initials_title():
    rest = " ".join(word.upper() for word in _words(random.randint(1, 4)))
    return f"{_pick(INITIALS)} {rest}"


def inline_period_title():
    parts = _sentence(random.randint(2, 5))
    parts.insert(random.randrange(len(parts) + 1), _pick(DOMAINS))
    return _join(parts)


def camel_title():
    parts = _sentence(random.randint(2, 5))
    parts.insert(random.randrange(len(parts) + 1), _pick(CAMEL))
    return _join(parts)


def slash_title():
    parts = _sentence(random.randint(1, 4))
    token = _pick(SLASHES)
    if random.random() < 0.5:
        token = f"{_pick(CONTENT)}/{_pick(SMALL_WORDS)}/{_pick(CONTENT)}"
    parts.insert(random.randrange(len(parts) + 1), token)
    return _join(parts)


def hyphen_title():
    parts = _sentence(random.randint(1, 4))
    token = _pick(HYPHENS)
    if random.random() < 0.5:
        token = f"{_pick(CONTENT)}-{_pick(SMALL_WORDS)}-{_pick(CONTENT)}"
    parts.insert(random.randrange(len(parts) + 1), token)
    return _join(parts)


def all_caps_title():
    parts = _words(random.randint(3, 7))
    if random.random() < 0.6:
        parts[random.randrange(1, len(parts) - 1)] = _pick(["a", "an", "and", "of", "the", "for", "to"])
    return " ".join(part.upper() for part in parts)


def acronym_title():
    parts = _sentence(random.randint(2, 5))
    parts.insert(random.randrange(len(parts) + 1), _pick(ACRONYMS))
    return _join(parts)


def leading_punct_title():
    body = _join(_sentence(random.randint(2, 6), vary=True))
    leader = _pick(LEADERS)
    closer = {"'": "'", '"': '"', "(": ")", "[": "]", "“": "”", "‘": "’", "*": ""}.get(leader, "")
    return f"{leader}{body}{closer}"


def subphrase_title():
    left = _join(_sentence(random.randint(2, 5)))
    right = _join(_words(random.randint(1, 3)))
    return f"{left}{_pick(SUB_MARKS)} {_pick(SMALL_WORDS)} {right}"


def weird_space_title():
    parts = _words(random.randint(2, 5))
    sep = _pick(["  ", "   ", "\t", "\t\t", " \t ", "\t ", "\u00a0", "\u200a", "\u2006"])
    return sep.join(parts)


def double_slash_title():
    host = _pick(["foo.com", "example.com", "bbc.co.uk"])
    parts = _sentence(random.randint(1, 3))
    parts.insert(random.randrange(len(parts) + 1), f"http://{host}")
    return _join(parts)


def combo_title():
    return _join([
        _pick(HONORIFICS),
        _pick(MC_WORDS),
        "and",
        _pick(["o'reilly", "d'artagnan", "l'amour", "o‘brien"]),
        _pick(CAMEL),
        _pick(ACRONYMS),
        _pick(HYPHENS),
        _pick(DOMAINS),
        ":",
        "the",
        _pick(CONTENT),
    ])


def unicode_title():
    parts = _sentence(random.randint(1, 3))
    parts.insert(random.randrange(len(parts) + 1), _pick(UNICODE_WORDS))
    if random.random() < 0.4:
        return " ".join(part.upper() for part in parts)
    return _join(parts)


def digits_title():
    parts = _sentence(random.randint(1, 4))
    parts.insert(random.randrange(len(parts) + 1), _pick(["34th", "3rd", "2nd", "5th", "Q&A", "AT&T", "2lmc"]))
    return _join(parts)


PATTERNS = [
    (8, normal_title),
    (4, small_middle),
    (3, small_edges),
    (3, apostrophe_title),
    (3, mc_title),
    (3, honorific_title),
    (2, initials_title),
    (3, inline_period_title),
    (3, camel_title),
    (3, slash_title),
    (3, hyphen_title),
    (3, all_caps_title),
    (3, acronym_title),
    (2, leading_punct_title),
    (4, subphrase_title),
    (3, weird_space_title),
    (2, double_slash_title),
    (2, combo_title),
    (2, unicode_title),
    (2, digits_title),
]
PATTERN_FUNCS = [fn for weight, fn in PATTERNS for _ in range(weight)]


def random_title():
    return random.choice(PATTERN_FUNCS)()


def _small_cases(frame):
    return [frame.format(w=word) for word in SMALL_WORDS]


def _sub_cases(left, right):
    return [f"{left}{mark} the {right}" for mark in SUB_MARKS]


def _space_cases(left, right):
    return [
        f"{left}\t{right}",
        f"{left}  {right}",
        f"{left}   {right}",
        f"{left}\t\t{right}",
        f"{left} \t {right}",
        f"{left}\u00a0{right}",
        f"{left}\u200a{right}",
        f"{left}\u2006{right}",
        f"{left}\tand  {right}",
    ]


def crafted_visible():
    lines = [
        "the quick brown fox",
        "hello world",
        "war and peace",
        "the end of the line for",
        "o'reilly and d'artagnan",
        "my name is o'reilly",
        "l'grange l'grange l'Grange l'Grange",
        "o'grange's O'grange's o'Grange's O'Grange's",
        "o‘reilly and d‘angelo",
        "ronald mcdonald",
        "Mr McTavish went to MacDonalds",
        "mac mc MAC MC machine",
        "mccay-mcbut-mcdo mcdonalds/mcby",
        "mcfoo-bar, MCFOO-BAR, McFoo-bar, McFoo-Bar, mcfoo-mcbar, foo-mcbar",
        "MRS SMITH",
        "mr holmes and dr watson",
        "Mr mr Mrs Ms Mss Dr dr , Mr. and Mrs. Person",
        "A.B.C IS HERE",
        "A.B SEES THE LIGHT",
        "WASHINGTON, D.C. SHOULD BE FIXED BUT MIGHT BE A PROBLEM",
        "visit example.com now",
        "this is something listed on del.icio.us",
        "this is http://foo.com",
        "the fooBar test",
        "iTunes should be unmolested",
        "sending UDP packets over PPPoE works great",
        "foo/bar",
        "a title and/or string",
        "dance with me/let’s face the music and dance",
        "mother-in-law",
        "a-b end-to-end two-not-three/three-by-four/five-and",
        "THIS IS A TEST",
        "THIS IS ALL CAPS AND SHOULD BE ADDRESSED",
        "the xkcd comic",
        "words with all consonants like cnn are acronyms",
        "(hello world)",
        "'by the Way, small word at the start but within quotes.'",
        "Small word at end is nothing to be afraid of",
        '"Nothing to be Afraid Of?"',
        "the lord of the rings: the fellowship",
        "still dead; a sequel follows",
        "are you sure? a warning",
        "stop now! a notice",
        "end of line. a new start",
        "famous line - a trick, perhaps",
        "episode 7 – the force awakens",
        "snakes on a plane — the tv edit",
        "horizontal mark ― a final clause",
        "a\tb",
        "text\twith\ttabs",
        "hello  world",
        "a mix\u00a0of\tdifferent\u200aspace\u2006characters",
        "a simple tcp and udp wrapper",
        "Q&A with steve jobs: 'that's what happens in technology'",
        "What is AT&T's problem?",
        "34th 3rd 2nd",
        "EL NIÑO A ARRIVÉ HIER",
        "ýæ ñø",
        "‘QUOTE’ A GREAT",
        "“YOUNG AND RESTLESS”",
        "oblon, spivak, mcclelland, maier & neustadt",
        "FOO BAR 5TH ST",
        "2lmc Spool: 'gruber on OmniFocus and vapo(u)rware'",
        "THE CASE OF X ≤ 7",
    ]
    lines.extend(_small_cases("journey {w} home"))
    lines.extend(_sub_cases("notes from the harbor", "voyage"))
    lines.extend(_space_cases("alpha", "beta"))
    return lines


def crafted_hidden():
    lines = [
        "a lantern above the quiet harbor",
        "good night moon",
        "crime and punishment",
        "a walk on the wild side of",
        "d'angelo met l'oreal",
        "her book is by o'brien",
        "l'amour l'amour L'amour L'Amour",
        "d'angelo's D'angelo's d'Angelo's D'Angelo's",
        "l‘amour and o‘malley",
        "ask mccarthy about the plan",
        "dr mckinley met mcgregor",
        "mac MAC mc MC press",
        "mcdo-mcby-mcfly mctavish/mcfoo",
        "mcbar-foo, MCBAR-FOO, McBar-foo, McBar-Foo, mcbar-mcfoo, bar-mcfoo",
        "DR WATSON",
        "ms marple and mr holmes",
        "ms MS mr MR mrs MRS dr DR Mss person",
        "J.R.R IS HERE",
        "N.Y FEELS THE RAIN",
        "REPORT FROM D.C. MUST STAY IN CAPS",
        "open nytimes.com today",
        "mail from bbc.co.uk arrived",
        "see https://example.com later",
        "an iPhone and a macOS update",
        "YouTube and JavaScript stay mixed",
        "PPPoE over a private line",
        "read/write",
        "north/south passage",
        "input/output and/or both",
        "editor-in-chief",
        "state-of-the-art well-known design",
        "ALL HANDS ON DECK",
        "PLEASE FILE THE REPORT FOR MONDAY",
        "html and css for the web",
        "the gps and lcd failed",
        "[hello harbor]",
        '"by the by, a quoted small word."',
        "nothing left to be afraid of",
        "'Nothing to be afraid of?'",
        "the return of the king: the journey",
        "hold fire; the captain waits",
        "who goes there? the watch",
        "brace now! the storm",
        "chapter one. the beginning",
        "second draft - the rewrite",
        "log book – the last entry",
        "final cut — the silent reel",
        "margin rule ― the extra note",
        "gamma\tdelta",
        "left\tmiddle\tright",
        "hidden  gap",
        "mix\u00a0these\todd\u200aspaces\u2006now",
        "a basic tcp and udp tunnel",
        "Q&A about AT&T and the 5th fleet",
        "2nd 3rd 34th",
        "CAFÉ NAÏVE RÉSUMÉ",
        "crème brûlée",
        "‘TITLE’ A SMALL",
        "“OLD AND NEW”",
        "mcclelland, mcmaier & mcneustadt",
        "BAR STREET 5TH AVE",
        "2lmc Note: 'omniFocus and vapo(u)rware today'",
        "the case of X ≤ 7",
    ]
    lines.extend(_small_cases("stories {w} science"))
    lines.extend(_sub_cases("signals from the canyon", "beacon"))
    lines.extend(_space_cases("gamma", "delta"))
    return lines


def _take(lines, seen, blocked):
    chosen = []
    for line in lines:
        if not _ok(line) or line in seen or line in blocked:
            continue
        chosen.append(line)
        seen.add(line)
    return chosen


def _fill(chosen, seen, blocked):
    guard = 0
    while len(chosen) < COUNT:
        guard += 1
        if guard > 1_000_000:
            raise SystemExit("could not generate enough unique titles")
        line = random_title()
        if not _ok(line) or line in seen or line in blocked:
            continue
        chosen.append(line)
        seen.add(line)


def _expected(lines):
    rendered = []
    for line in lines:
        result = titlecase(line)
        if "\n" in result or "\r" in result:
            raise SystemExit(f"titlecase() introduced a newline for {line!r}")
        rendered.append(result)
    return rendered


def _write(path, lines):
    path.write_bytes("".join(f"{line}\n" for line in lines).encode("utf-8"))


def _assert_coverage(lines):
    blob_parts = []
    has_all_caps = False
    has_tab = False
    has_double_space = False
    has_nbsp = False
    for line in lines:
        blob_parts.append(line)
        if line.upper() == line and any(ch.isalpha() for ch in line):
            has_all_caps = True
        if "\t" in line:
            has_tab = True
        if "  " in line:
            has_double_space = True
        if "\u00a0" in line or "\u200a" in line or "\u2006" in line:
            has_nbsp = True
    blob = "\n".join(blob_parts)
    needles = [
        "o'",
        "d'",
        "l'",
        "mc",
        "MRS",
        "A.B",
        ".com",
        "fooBar",
        "/",
        "-",
        "xkcd",
        " and ",
        ": the",
        "://",
        "tcp",
        "udp",
        "Q&A",
    ]
    missing = [needle for needle in needles if needle not in blob and needle.lower() not in blob.lower()]
    if missing or not (has_all_caps and has_tab and has_double_space and has_nbsp):
        raise SystemExit(
            "missing rule coverage: "
            + ", ".join(missing)
            + f" caps={has_all_caps} tab={has_tab} spaces={has_double_space} unicode_space={has_nbsp}"
        )


def main():
    random.seed(1)
    seen = set()
    hidden_fixed = crafted_hidden()
    blocked = set(hidden_fixed)
    visible = _take(crafted_visible(), seen, blocked)
    _fill(visible, seen, blocked)

    hidden = _take(hidden_fixed, seen, set())
    _fill(hidden, seen, set())

    if len(visible) != COUNT or len(hidden) != COUNT:
        raise SystemExit(f"unexpected sizes: {len(visible)} visible, {len(hidden)} hidden")
    if set(visible) & set(hidden):
        raise SystemExit("visible and hidden titles overlap")

    visible_expected = _expected(visible)
    hidden_expected = _expected(hidden)
    _assert_coverage(visible)
    _assert_coverage(hidden)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    files = {
        DATA_DIR / "inputs.txt": visible,
        DATA_DIR / "expected.txt": visible_expected,
        DATA_DIR / "hidden_inputs.txt": hidden,
        DATA_DIR / "hidden_expected.txt": hidden_expected,
    }
    for path, lines in files.items():
        _write(path, lines)

    for path in files:
        payload = path.read_bytes()
        parts = payload.split(b"\n")
        if payload.count(b"\n") != COUNT or parts[-1] != b"" or len(parts) != COUNT + 1:
            raise SystemExit(f"{path.name} does not contain {COUNT} lines")
        if b"\r" in payload:
            raise SystemExit(f"{path.name} contains CR")
        print(f"{path.name} {COUNT}")


if __name__ == "__main__":
    main()
