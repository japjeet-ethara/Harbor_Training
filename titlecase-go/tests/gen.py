"""Generate fixed titlecase inputs and expected output from the original library.

Expected files are produced only by calling titlecase() in ../python-titlecase.
"""

import random
import sys
from pathlib import Path

SEED = 1
COUNT = 2000

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
ORIGINAL = HERE.parent.parent / "python-titlecase"

# Single-line inputs from NOTES.md. These are the cases a plain capitaliser
# gets wrong. Multiline notes are included as their individual lines, because
# each generated title has to stay on one line.
NOTE_INPUTS = [
    "Line number one",
    "and Line three",
    "afraid of",
    "WASHINGTON, D.C. SHOULD BE FIXED BUT MIGHT BE A PROBLEM",
    "l'grange",
    "l'GranGe",
    "d'angelo",
    "o'reilly",
    "o'grange",
    "o'grange's",
    "O'GranGe",
    "o'clock",
    "l‘grange",
    "mcclelland",
    "mcdonalds",
    "macdonalds",
    "MacDonalds",
    "mc",
    "MC",
    "mac",
    "mr smith",
    "MRS",
    "ms",
    "dr who",
    "this is just an example.com",
    "del.icio.us",
    "http://foo.com",
    "iTunes should be unmolested",
    "this v that",
    "this v. that",
    "this vs that",
    "this vs. that",
    "word/word",
    "a title and/or string",
    "foo//bar",
    "end-to-end",
    "THIS IS ALL CAPS AND SHOULD BE ADDRESSED",
    "words like cnn",
    "5th st",
    "34th 3rd 2nd",
    "a thing",
    "'by the Way, small word at the start but within quotes.'",
    "Small word at end is nothing to be afraid of",
    "Starting Sub-Phrase With a Small Word: a Trick, Perhaps?",
    "Sub-Phrase With a Small Word in Quotes: 'a Trick, Perhaps?'",
    'sub-phrase with a small word in quotes: "a trick, perhaps?"',
    "Starting a Hyphen Delimited Sub-Phrase With a Small Word - a Trick, Perhaps?",
    "Starting an Em Dash Delimited Sub-Phrase With a Small Word — a Trick, Perhaps?",
    "text\twith\ttabs",
    "a mix\u00a0of\tdifferent\u200aspace\u2006characters",
    "this shouldn't",
    "get mangled",
    "this shouldn't get mangled",
    "Q&A with steve jobs: 'that's what happens in technology'",
    "What is AT&T's problem?",
    "Apple deal with AT&T falls through",
    "The SEC's Apple probe: what you need to know",
    '"Nothing to Be Afraid of?"',
    "2lmc Spool: 'gruber on OmniFocus and vapo(u)rware'",
    "reading between the lines of steve jobs's 'thoughts on music'",
    "generalissimo francisco franco: still dead; kieren McCarthy: still a jackass",
    "Mr McTavish went to MacDonalds",
    "mac mc MAC MC machine",
    "FOO BAR 5TH ST",
    "EL NIÑO A ARRIVÉ HIER",
    "‘QUOTE’ A GREAT",
    "“YOUNG AND RESTLESS”",
    "mccay-mcbut-mcdo mcdonalds/mcby",
    "mcfoo-bar, MCFOO-BAR, McFoo-bar, mcfoo-mcbar, foo-mcbar",
    "o'melveny/o'doyle",
]

SMALL = [
    "a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in",
    "of", "on", "or", "the", "to", "v", "v.", "via", "vs", "vs.",
]
NORMAL = [
    "apple", "bridge", "castle", "river", "market", "garden", "silver",
    "window", "paper", "orange", "music", "yellow", "purple", "circle",
    "family", "history", "public", "private", "morning", "evening",
    "summer", "winter", "letter", "number", "people", "little", "water",
    "house", "world", "light", "stone", "field", "cloud", "dream",
    "quiet", "bright", "simple", "common", "second", "travel",
]
APOS_REST = [
    "grange", "reilly", "clock", "angelo", "melveny", "doyle",
    "GranGe", "grange's", "Reilly",
]
INTERNAL = ["iTunes", "iPhone", "AT&T", "OmniFocus", "PhD", "McDonald", "eBay"]
DOMAINS = ["example.com", "del.icio.us", "http://foo.com", "blog.example.co.uk"]
INITIALS = ["D.C.", "A.B", "A.B.", "U.S.", "U.S.A."]
HONORIFICS = ["mr", "MR", "Mr", "mrs", "MRS", "ms", "MS", "dr", "DR", "Dr"]
ACRONYMS = ["cnn", "html", "gps", "php", "nfl", "ibm"]
SHORT_CONSONANTS = ["st", "nd", "rd", "5th", "3rd", "2nd", "34th"]
SUBPHRASE = [": ", ". ", "; ", "? ", "! ", " - ", " – ", " — ", " ― "]


def join_parts(parts):
    sep = random.choice([" ", " ", " ", "\t", "\u00a0", "\u200a", "\u2006", "  "])
    return sep.join(parts)


def normal_word():
    word = random.choice(NORMAL)
    roll = random.random()
    if roll < 0.15:
        return word.upper()
    if roll < 0.30:
        return word.capitalize()
    return word


def tricky_token():
    kind = random.randrange(12)
    if kind == 0:
        first = random.choice("dloDLO")
        mark = random.choice(["'", "‘"])
        return first + mark + random.choice(APOS_REST)
    if kind == 1:
        return random.choice(["mc", "Mc", "MC", "mac", "Mac"]) + random.choice(
            ["clelland", "donalds", "tavish", "foo", "bar", "carthy"]
        )
    if kind == 2:
        return random.choice(HONORIFICS)
    if kind == 3:
        return random.choice(DOMAINS)
    if kind == 4:
        return random.choice(INTERNAL)
    if kind == 5:
        return random.choice(SMALL)
    if kind == 6:
        left = random.choice(NORMAL + SMALL)
        right = random.choice(NORMAL + SMALL)
        return left + "/" + right
    if kind == 7:
        return random.choice(NORMAL) + "//" + random.choice(NORMAL)
    if kind == 8:
        bits = [random.choice(NORMAL + SMALL) for _ in range(random.randint(2, 4))]
        return "-".join(bits)
    if kind == 9:
        return random.choice(ACRONYMS + SHORT_CONSONANTS)
    if kind == 10:
        return random.choice(INITIALS)
    return random.choice(["Q&A", "AT&T", "'by", '"Nothing', "“young"])


def one_title():
    if random.random() < 0.18:
        base = random.choice(NOTE_INPUTS)
        if random.random() < 0.55:
            return base
        extra = [normal_word() for _ in range(random.randint(1, 3))]
        if random.random() < 0.5:
            return join_parts(extra + [base])
        return join_parts([base] + extra)

    parts = [tricky_token() if random.random() < 0.55 else normal_word()
             for _ in range(random.randint(3, 9))]
    if random.random() < 0.7:
        parts[0] = random.choice(SMALL)
    if random.random() < 0.7:
        parts[-1] = random.choice(SMALL)
    if random.random() < 0.45:
        at = random.randrange(len(parts))
        parts[at] = parts[at] + random.choice(SUBPHRASE) + random.choice(SMALL)
    title = join_parts(parts)
    if random.random() < 0.14:
        title = title.upper()
    return title


def generate(count, forbidden=()):
    banned = set(forbidden)
    titles = []
    seen = set()
    while len(titles) < count:
        title = one_title()
        if "\n" in title or "\r" in title or title == "" or title in banned or title in seen:
            continue
        seen.add(title)
        titles.append(title)
    return titles


def write_lines(path, lines):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for line in lines:
            handle.write(line + "\n")


def expected_for(lines, titlecase):
    results = []
    for line in lines:
        result = titlecase(line)
        if "\n" in result or "\r" in result:
            raise SystemExit("titlecase() returned more than one line")
        results.append(result)
    return results


def main():
    random.seed(SEED)
    sys.path.insert(0, str(ORIGINAL))
    from titlecase import titlecase

    public = generate(COUNT)
    hidden = generate(COUNT, public)
    if public == hidden:
        raise SystemExit("hidden inputs matched the public inputs")

    write_lines(DATA / "inputs.txt", public)
    write_lines(DATA / "hidden_inputs.txt", hidden)
    write_lines(DATA / "expected.txt", expected_for(public, titlecase))
    write_lines(DATA / "hidden_expected.txt", expected_for(hidden, titlecase))


if __name__ == "__main__":
    main()
