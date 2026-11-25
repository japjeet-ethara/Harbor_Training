#!/usr/bin/env python3
"""Generate test titles and their expected output.

Writes four files to tests/data/:
    inputs.txt, expected.txt                 2000 titles and their results
    hidden_inputs.txt, hidden_expected.txt   2000 different titles and results

Every expected line comes from running the original titlecase() from
../environment/python-titlecase. No expected output is written by hand.

Files are read and written as UTF-8 with "\n" line endings. Read them by
splitting on "\n" only: str.splitlines() also splits on other characters.
"""

import os
import random
import sys

sys.dont_write_bytecode = True  # keep __pycache__ out of python-titlecase

HERE = os.path.dirname(os.path.realpath(__file__))
REPO = os.path.realpath(os.path.join(HERE, "..", "environment", "python-titlecase"))
DATA = os.path.join(HERE, "data")
COUNT = 2000

sys.path.insert(0, REPO)
import titlecase as original  # noqa: E402

if not os.path.realpath(original.__file__).startswith(REPO + os.sep):
    sys.exit("Wrong titlecase module loaded: " + original.__file__)
if original.REGEX_AVAILABLE:
    sys.exit("The regex package is installed. instruction.md names the re "
             "fallback as the reference, so run this without regex.")

NORMAL = """
adventure ancient autumn beautiful bridge broken castle city clever cold
daughter dark dream early earth evening falling father field fire forest
friend garden golden green guide hidden history home house journey kingdom
lake last letter light little long machine memory mirror moon morning mother
mountain music night ocean old open orange paper people quiet rain river road
secret shadow silent silver small stone story storm summer sun teacher time
tomorrow tree village water winter woman world young
""".split()

SMALL = ("a an and as at but by en for if in of on or the to "
         "v v. via vs vs.").split()

# One list per rule in NOTES.md, including its surprising results.
TRICKY = {
    "small": SMALL,
    "small_cased": ["The", "THE", "Of", "OF", "AND", "And", "To", "VS.", "V."],
    "initials": ["J.R.R.", "V.", "A.", "Q.", "U.S.A.", "J.", "T.S.", "A.B"],
    "apostrophe": ["o'reilly", "o'neil", "d'artagnan", "d'angelo's", "l'oreal",
                   "l'amour", "O'REILLY", "D'ARTAGNAN", "o‘brien",
                   "d‘arcy", "don't", "it's", "rock'n'roll"],
    "mc": ["mcdonald", "mcgregor", "mcdonald's", "MCDONALD", "McKay", "mcat",
           "mcp", "mc", "macdonald", "mcx", "Mcintosh", "mc-donald"],
    "title": ["mr", "mrs", "ms", "dr", "Mr", "MR", "MRS", "MS", "DR", "mr.",
              "dr.", "mrs."],
    "period": ["example.com", "node.js", "e.g.", "i.e.", "www.example.org",
               "v1.2", "a.b", "http://example.com/foo", "end.", "...", "3.14"],
    "inner_caps": ["iPhone", "eBay", "NASA", "YouTube", "LaTeX", "macOS",
                   "inDesign", "aND", "IPHONE", "ofTen", "toDo"],
    "slash": ["and/or", "either/or", "his/her", "input/output", "a/b/c",
              "http://foo/bar", "//foo/bar", "/usr/bin", "of/the", "AND/OR"],
    "hyphen": ["mother-in-law", "state-of-the-art", "self-made", "well-known",
               "x-ray", "e-mail", "-start", "end-", "WELL-KNOWN", "a-b", "-",
               "--"],
    "consonant": ["bbc", "html", "xml", "css", "nfl", "pdf", "sql", "hmm",
                  "psst", "tsk", "st", "BBC", "HTML", "gym", "rhythm", "cry",
                  "bbc's"],
    "first_last": ["(the", "of)", "\"a", "good\"", "'the", "for?", "to!",
                   "in.", "on,", "at;", "[of]", "“the", "‘a"],
    "subphrase": ["wars: a", "stop. the", "wait - a", "wait — of",
                  "wait – the", "why? an", "yes! in", "well; to",
                  "foo: inDesign", "end: or"],
    "unicode": ["café", "éclair", "naïve", "straße",
                "ﬁn", "über", "ωmega", "ÉCOLE", "ßeta",
                "ǆabc", "İstanbul", "ŉabc", "привет",
                "日本語", "éTat", "«été»"],
    "digits": ["3d", "2nd", "1984", "7up", "100%", "$5", "#1", "4x4", "12"],
}
CATEGORIES = list(TRICKY)

# Whole-title inputs taken from NOTES.md. Inputs only, never expected results.
LITERALS = [
    "", "   ",
    "the lord of the rings", "THE LORD OF THE RINGS", "JOHN V. SMITH",
    "john v. smith", "o'reilly media", "d'artagnan rides", "l'oreal paris",
    "mcdonald farm", "MCDONALD FARM", "macdonald farm",
    "visit mr smith and dr jones", "visit example.com today",
    "the iPhone and eBay story", "NASA rocks", "war and peace",
    "war AND peace", "read this and/or that", "mother-in-law",
    "HELLO WORLD", "the bbc and the html spec", "st john", "'hello' world",
    "(the end) of it", "what is it good for?", "the end of",
    "a  tale\tof two", "star wars: a new hope", "wait - a moment",
    "wait — a moment", "O'REILLY MEDIA", "MR SMITH AND MRS JONES",
    "IPHONE", "mcat exam", "hmm that is odd", "this and/or",
    "foo: inDesign rocks", "http://foo/bar now", "see //foo/bar now",
    "U.S.A. TODAY", "AND/OR LOGIC", "WELL-KNOWN FACT", "MS PAINT", "ms paint",
]


def join(tokens):
    """Join tokens, mostly with single spaces."""
    text = tokens[0]
    for token in tokens[1:]:
        text += random.choices(
            [" ", "  ", "\t", " ", " "], [90, 4, 2, 3, 1])[0] + token
    roll = random.random()
    if roll < 0.02:
        text = " " + text
    elif roll < 0.04:
        text += " "
    return text


def recase(text):
    """Change the case of a whole title."""
    style = random.choices(["keep", "upper", "capitalised"], [65, 22, 13])[0]
    if style == "upper":
        return text.upper()
    if style == "capitalised":
        return " ".join(word.capitalize() for word in text.split(" "))
    return text


def make_title(index):
    """Build a title, cycling through the categories so each gets used."""
    tokens = [random.choice(NORMAL) for _ in range(random.randint(1, 6))]
    for _ in range(random.randint(0, 2)):
        tokens.insert(random.randint(0, len(tokens)), random.choice(SMALL))
    forced = CATEGORIES[index % len(CATEGORIES)]
    tokens.insert(random.randint(0, len(tokens)), random.choice(TRICKY[forced]))
    if random.random() < 0.35:
        extra = random.choice(CATEGORIES)
        tokens.insert(random.randint(0, len(tokens)),
                      random.choice(TRICKY[extra]))
    return recase(join(tokens))


def fill(titles, seen, index):
    """Add new titles until the list has COUNT of them."""
    while len(titles) < COUNT:
        title = make_title(index)
        index += 1
        if title not in seen:
            seen.add(title)
            titles.append(title)
    random.shuffle(titles)
    return index


def write_lines(name, lines):
    # newline="\n" stops Windows from writing \r\n.
    with open(os.path.join(DATA, name), "w", encoding="utf-8",
              newline="\n") as handle:
        handle.write("".join(line + "\n" for line in lines))


def run_original(titles):
    results = [original.titlecase(title) for title in titles]
    for title, result in zip(titles, results):
        # A line break in either would stop the files lining up line by line.
        if any(mark in title for mark in "\r\n") or "\n" in result:
            sys.exit("Title breaks one-per-line format: %r" % title)
    return results


def main():
    random.seed(1)
    os.makedirs(DATA, exist_ok=True)

    literals = list(dict.fromkeys(LITERALS))
    random.shuffle(literals)
    inputs, hidden = literals[0::2], literals[1::2]
    seen = set(literals)  # membership only: set order is not repeatable

    index = fill(inputs, seen, 0)
    fill(hidden, seen, index)

    assert len(inputs) == len(hidden) == COUNT
    assert not set(inputs) & set(hidden)

    write_lines("inputs.txt", inputs)
    write_lines("expected.txt", run_original(inputs))
    write_lines("hidden_inputs.txt", hidden)
    write_lines("hidden_expected.txt", run_original(hidden))
    print("Wrote %d + %d titles to %s" % (len(inputs), len(hidden), DATA))


if __name__ == "__main__":
    main()
