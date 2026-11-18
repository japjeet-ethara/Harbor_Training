#!/usr/bin/env python3
"""Generate deterministic titlecase fixtures from the original library."""

import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "environment" / "python-titlecase"))

import titlecase as titlecase_module
from titlecase import titlecase

if titlecase_module.REGEX_AVAILABLE:
    sys.stderr.write(
        "error: titlecase.REGEX_AVAILABLE is True; "
        "the optional regex package must not be installed\n"
    )
    raise SystemExit(1)

# Pre-titlecase inputs from NOTES.md. Blank lines and tabs are omitted because
# a title here cannot contain them. Expected text is never stored; titlecase()
# is called with its default arguments.
NOTES_INPUTS = [
    "the udp wrapper",
    "WASHINGTON, D.C. SHOULD BE FIXED BUT MIGHT BE A PROBLEM",
    "o'grange",
    "mcdonald",
    "mrs",
    "this is just an example.com",
    "iTunes should be unmolested",
    "this v that",
    "word/word",
    "end-to-end",
    "THIS IS ALL CAPS AND SHOULD BE ADDRESSED",
    "words with all consonants like cnn are acronyms",
    "'hello'",
    "'by the Way, small word at the start but within quotes.'",
    "Small word at end is nothing to be afraid of",
    "Starting Sub-Phrase With a Small Word: a Trick, Perhaps?",
]

SMALL = [
    "a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in",
    "of", "on", "or", "the", "to", "v", "v.", "via", "vs", "vs.",
]

NORMAL = [
    "apple", "bridge", "castle", "market", "river", "garden", "forest",
    "silver", "golden", "quiet", "bright", "stone", "harbor", "window",
    "paper", "music", "thought", "people", "history", "science", "winter",
    "summer", "orange", "purple", "yellow", "circle", "square", "letter",
    "number", "public", "private", "simple", "double", "single", "north",
    "south", "east", "west", "captain", "general", "soldier", "artist",
    "writer", "reader", "player", "city", "village", "island", "ocean",
    "mountain", "valley", "cloud", "storm", "light", "shadow", "dream",
    "story", "title", "chapter", "volume", "series", "report", "update",
    "future", "past", "present", "morning", "evening", "monday", "friday",
    "copper", "iron", "glass", "wooden", "digital", "remote", "local",
    "global", "inner", "outer", "early", "final", "open", "closed",
    "happy", "serious", "famous", "common", "rare", "young", "fresh",
    "clear", "whole", "other", "same", "next", "main", "washington",
    "problem", "quotes", "trick", "perhaps", "afraid", "nothing", "start",
    "niño", "crème", "brûlée", "arrivé", "hier", "franco", "jobs",
    "line", "three", "hello", "unmolested",
]

TRICKS = [
    "apos",
    "mc",
    "honorific",
    "host",
    "camel",
    "slash",
    "hyphen",
    "acronym",
    "short_consonant",
    "ordinal",
    "quoted",
    "subphrase",
    "small_edges",
    "url",
    "ampersand",
    "initials",
]

HOSTS = [
    "example.com",
    "del.icio.us",
    "foo.bar",
    "mail.example.org",
    "news.co.uk",
    "static.cdn.net",
    "foo.bar.baz",
]

CAMEL = [
    "iTunes", "iPhone", "iPad", "eBay", "macOS", "OmniFocus",
    "YouTube", "PowerPoint",
]

SUB_SEPS = [
    ": ", "; ", "? ", "! ", ". ", "- ",
    "\u2013 ", "\u2012 ", "\u2014 ", "\u2015 ",
]

COUNT = 2000


def usable(line):
    if line.strip() == "":
        return False
    return "\n" not in line and "\r" not in line and "\t" not in line


def stylize(line, style):
    if style == "lower":
        return line.lower()
    if style == "upper":
        return line.upper()
    return line


def style_for(index):
    slot = index % 10
    if slot == 0:
        return "lower"
    if slot == 1:
        return "upper"
    return "mixed"


def initials(rng):
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    parts = []
    groups = 1 + rng.randrange(3)
    for _ in range(groups):
        if rng.randrange(2) == 0:
            parts.append(rng.choice(letters) + ".")
        else:
            parts.append(rng.choice(letters) + "." + rng.choice(letters))
    return "".join(parts)


def apos(rng):
    first = rng.choice("dolDOL")
    mark = "'" if rng.randrange(2) == 0 else "\u2018"
    rest = rng.choice([
        "grange", "reilly", "malley", "angelo", "esprit", "doyle", "melveny",
    ])
    form = rng.randrange(3)
    if form == 1:
        rest = rest.capitalize()
    elif form == 2:
        rest = rest.upper()
    token = first + mark + rest
    if rng.randrange(2) == 0:
        token += "'s"
    return token


def mc(rng):
    prefix = rng.choice(["mc", "Mc", "MC"])
    rest = rng.choice([
        "donald", "donalds", "clelland", "tavish", "maier", "neustadt",
        "foo", "bar", "cay",
    ])
    if rng.randrange(3) == 0:
        rest += "-" + rng.choice(["bar", "to", "and", "mcbar"])
    return prefix + rest


def honorific(rng):
    word = rng.choice(["mr", "mrs", "ms", "dr"])
    form = rng.randrange(4)
    if form == 0:
        return word
    if form == 1:
        return word.upper()
    if form == 2:
        return word.capitalize()
    chars = []
    for i, ch in enumerate(word):
        chars.append(ch.upper() if i % 2 else ch)
    return "".join(chars)


def camel(rng):
    if rng.randrange(2) == 0:
        return rng.choice(CAMEL)
    base = rng.choice(NORMAL)
    if len(base) == 1:
        return "i" + base.upper()
    return base[0] + base[1:].capitalize()


def slash(rng):
    pool = NORMAL + SMALL + ["word"]
    parts = [rng.choice(pool) for _ in range(2 + rng.randrange(2))]
    return "/".join(parts)


def hyphen(rng):
    pool = [
        "end", "to", "not", "three", "by", "four", "five", "and", "word",
        "state", "of", "the", "art", "all",
    ]
    parts = [rng.choice(pool) for _ in range(2 + rng.randrange(3))]
    return "-".join(parts)


def acronym(rng):
    known = ["cnn", "bbc", "html", "ftp", "gps", "nfl", "sql", "css"]
    if rng.randrange(4) == 0:
        return rng.choice(known)
    consonants = "bcdfghjklmnpqrstvwxz"
    return "".join(rng.choice(consonants) for _ in range(3 + rng.randrange(4)))


def short_consonant(rng):
    return rng.choice(["st", "ft", "pm", "bc", "tv", "dj"])


def ordinal(rng):
    return rng.choice([
        "1st", "2nd", "3rd", "4th", "5th", "11th", "21st", "34th", "100th",
    ])


def quoted(rng):
    word = rng.choice(NORMAL + ["hello"])
    wraps = [
        ("'", "'"),
        ("\u2018", "\u2019"),
        ('"', '"'),
        ("\u201c", "\u201d"),
    ]
    left, right = wraps[rng.randrange(len(wraps))]
    return left + word + right


def ampersand(rng):
    return rng.choice(["AT&T", "Q&A", "R&D", "S&P", "at&t", "q&a"])


def url(rng):
    scheme = "https://" if rng.randrange(2) else "http://"
    return scheme + rng.choice(HOSTS)


def token_for(rng, trick):
    makers = {
        "apos": apos,
        "mc": mc,
        "honorific": honorific,
        "host": lambda r: r.choice(HOSTS),
        "camel": camel,
        "slash": slash,
        "hyphen": hyphen,
        "acronym": acronym,
        "short_consonant": short_consonant,
        "ordinal": ordinal,
        "quoted": quoted,
        "url": url,
        "ampersand": ampersand,
        "initials": initials,
    }
    token = makers[trick](rng)
    if token == "" or any(ch in token for ch in " \n\r\t"):
        raise SystemExit("bad token from %s: %r" % (trick, token))
    return token


def base_tokens(rng):
    count = 4 + rng.randrange(5)
    tokens = [rng.choice(NORMAL) for _ in range(count)]
    tokens[rng.randrange(1, count - 1)] = rng.choice(SMALL)
    return tokens


def subphrase_line(rng, tokens):
    sep = SUB_SEPS[rng.randrange(len(SUB_SEPS))]
    tail = [rng.choice(SMALL)]
    for _ in range(1 + rng.randrange(3)):
        tail.append(rng.choice(NORMAL))
    if rng.randrange(3) == 0:
        tail[0] = rng.choice(["'", "\u2018", '"', "\u201c"]) + tail[0]
    return " ".join(tokens) + sep + " ".join(tail)


def small_edge_line(rng, tokens):
    tokens = list(tokens)
    lead = rng.choice(["", "'", "\u2018", '"', "\u201c", "("])
    trail = rng.choice(["", ".", "?", "!", ",", ":", ";"])
    tokens[0] = lead + rng.choice(SMALL)
    tokens[-1] = rng.choice(SMALL) + trail
    return " ".join(tokens)


def compose(rng, trick):
    tokens = base_tokens(rng)
    if trick == "subphrase":
        return subphrase_line(rng, tokens)
    if trick == "small_edges":
        return small_edge_line(rng, tokens)
    tokens = list(tokens)
    tokens[rng.randrange(len(tokens))] = token_for(rng, trick)
    return " ".join(tokens)


def fill(rng, seen, count, seed_lines):
    lines = []
    for line in seed_lines:
        if not usable(line):
            raise SystemExit("seed title is not a single line: %r" % (line,))
        if line in seen:
            raise SystemExit("duplicate seed title: %r" % (line,))
        seen.add(line)
        lines.append(line)
    failures = 0
    while len(lines) < count:
        if failures > 10000:
            raise SystemExit("could not generate enough unique titles")
        made = len(lines) - len(seed_lines)
        style = style_for(made)
        trick = TRICKS[(made // 10) % len(TRICKS)]
        line = stylize(compose(rng, trick), style)
        if not usable(line) or line in seen:
            failures += 1
            continue
        result = titlecase(line)
        if result.strip() == "" or "\n" in result or "\r" in result:
            failures += 1
            continue
        failures = 0
        seen.add(line)
        lines.append(line)
    return lines


def write_lines(path, lines):
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = "\n".join(lines) + "\n"
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)


def read_lines(path):
    text = path.read_text(encoding="utf-8")
    if not text.endswith("\n") or "\r" in text:
        raise SystemExit("%s is not UTF-8 lines joined with \\n" % (path,))
    lines = text.split("\n")[:-1]
    if any(line == "" or "\t" in line for line in lines):
        raise SystemExit("%s contains a blank line or a tab" % (path,))
    return lines


def main():
    rng = random.Random(1)
    seen = set()
    visible = fill(rng, seen, COUNT, NOTES_INPUTS)
    hidden = fill(rng, seen, COUNT, [])

    data = ROOT / "tests" / "data"
    visible_in = data / "inputs.txt"
    hidden_in = data / "hidden_inputs.txt"
    visible_out = data / "expected.txt"
    hidden_out = data / "hidden_expected.txt"

    write_lines(visible_in, visible)
    write_lines(hidden_in, hidden)
    write_lines(visible_out, [titlecase(line) for line in visible])
    write_lines(hidden_out, [titlecase(line) for line in hidden])

    loaded_visible = read_lines(visible_in)
    loaded_hidden = read_lines(hidden_in)
    if loaded_visible != visible or loaded_hidden != hidden:
        raise SystemExit("reread inputs do not match the generated titles")
    if [titlecase(line) for line in loaded_visible] != read_lines(visible_out):
        raise SystemExit("expected.txt does not match titlecase()")
    if [titlecase(line) for line in loaded_hidden] != read_lines(hidden_out):
        raise SystemExit("hidden_expected.txt does not match titlecase()")
    if set(loaded_visible) & set(loaded_hidden):
        raise SystemExit("hidden titles overlap the visible set")
    if len(loaded_visible) != COUNT or len(set(loaded_visible)) != COUNT:
        raise SystemExit("visible set is not %s distinct titles" % (COUNT,))
    if len(loaded_hidden) != COUNT or len(set(loaded_hidden)) != COUNT:
        raise SystemExit("hidden set is not %s distinct titles" % (COUNT,))


if __name__ == "__main__":
    main()
