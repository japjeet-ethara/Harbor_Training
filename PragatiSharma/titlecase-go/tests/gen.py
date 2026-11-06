"""Generate reproducible titlecase inputs and frozen reference answers.

Answers come only from the original Python titlecase() function.
"""

import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ORIGINAL = (HERE.parent / ".." / "python-titlecase").resolve()
DATA = HERE / "data"

REQUIRED = (
    "visit http://example.com for the details",
    "see http://example now",
)

# Documented inputs from NOTES.md that do not contain a line break.
# The multi-line blank-line example is omitted on purpose.
NOTES_CASES = (
    "text\twith\ttabs",
    "a simple tcp and udp wrapper",
    "THIS IS ALL CAPS AND SHOULD BE ADDRESSED",
    "WASHINGTON, D.C. SHOULD BE FIXED BUT MIGHT BE A PROBLEM",
    "l'grange",
    "mcclelland",
    "dr",
    "iTunes should be unmolested",
    "this is a test",
    "word/word",
    "end-to-end",
    "Words with all consonants like cnn are acronyms",
    "hello world",
    "'by the Way, small word at the start but within quotes.'",
    "Small word at end is nothing to be afraid of",
    "Starting Sub-Phrase With a Small Word: a Trick, Perhaps?",
    "https://example.com",
    "www.example.com",
)

LINE_BREAKS = set("\n\r\v\f\x1c\x1d\x1e\x85\u2028\u2029")

WORDS = (
    "apple", "bridge", "castle", "market", "river", "golden", "silent",
    "paper", "winter", "public", "report", "history", "science", "music",
    "garden", "silver", "harbor", "letter", "orange", "purple", "window",
    "family", "school", "office", "travel", "summer", "autumn", "spring",
    "monday", "friday", "london", "paris", "boston", "denver", "copper",
    "marble", "velvet", "crystal", "forest", "island", "valley", "canyon",
    "signal", "rocket", "button", "candle", "mirror", "pocket", "thread",
    "anchor", "beacon", "cobalt", "dragon", "engine", "falcon", "gravel",
    "hammer", "indigo", "jigsaw", "kettle", "lantern", "magnet", "nectar",
    "oasis", "pebble", "quartz", "ribbon", "saddle", "timber", "umbrella",
    "voyage", "walnut", "yellow", "zenith", "author", "border", "camera",
)

SMALL = (
    "a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in",
    "of", "on", "or", "the", "to", "v", "v.", "via", "vs", "vs.",
)

ACRONYMS = ("cnn", "html", "gps", "nbc", "fbi", "cia", "rss", "xml", "css", "php", "sql", "nfl")
APOS_PREFIXES = ("d", "l", "o", "D", "L", "O")
APOS_STEMS = ("grange", "angelo", "malley", "clock", "connor", "hiver", "eaux", "oeuvre")
MC_REST = ("clelland", "donald", "maier", "neustadt", "intosh", "kay", "foo", "bar", "byrne")
MC_PREFIXES = ("mc", "Mc", "MC")
HONORIFICS = ("mr", "mrs", "ms", "dr", "MR", "MRS", "MS", "DR", "Mr", "Dr")
QUOTES = ("'", '"', "“", "‘", "”")
SUB_BREAKS = (": ", ". ", "; ", "? ", "! ", "- ", "– ", "‒ ", "— ", "― ")
SPACES = ("\t", "  ", "   ", "\u00a0", "\t\t", "\u200a", "\u2006", " \t ")
INTERNAL_CAPS = ("iTunes", "eBay", "IPv6", "PhD", "YouTube", "McDonald")


def has_line_break(text):
    return any(ch in LINE_BREAKS for ch in text)


def load_titlecase():
    source = ORIGINAL / "titlecase" / "__init__.py"
    if not source.is_file():
        raise SystemExit(f"Original titlecase source not found: {source}")
    sys.path.insert(0, str(ORIGINAL))
    import titlecase as titlecase_mod

    if titlecase_mod.REGEX_AVAILABLE:
        raise SystemExit(
            "REGEX_AVAILABLE is True in "
            f"{Path(titlecase_mod.__file__).resolve()}. "
            "Reference answers must use Python's standard-library re implementation, "
            "without the optional third-party regex package."
        )
    return titlecase_mod


def word():
    return random.choice(WORDS)


def words(count):
    return [word() for _ in range(count)]


def maybe_case(text):
    roll = random.randrange(5)
    if roll == 0:
        return text.upper()
    if roll == 1:
        return text.lower()
    return text


def ordinary():
    parts = words(random.randint(2, 8))
    style = random.randrange(4)
    if style == 1:
        parts = [part.capitalize() for part in parts]
    elif style == 2:
        parts = [part.upper() for part in parts]
    elif style == 3:
        parts[random.randrange(len(parts))] = random.choice(INTERNAL_CAPS)
    if random.random() < 0.25:
        parts.append(str(random.randint(1, 99)) + random.choice(("th", "st", "nd", "rd")))
    return " ".join(parts)


def small_words():
    parts = [word(), random.choice(SMALL), word(), random.choice(SMALL), word()]
    if random.random() < 0.5:
        parts.insert(0, random.choice(SMALL))
    if random.random() < 0.5:
        parts.append(random.choice(SMALL))
    if random.random() < 0.45:
        parts.insert(random.randint(1, len(parts) - 1), random.choice(SUB_BREAKS).rstrip())
        # Keep the break attached to the following small word as its own tokens.
    text = []
    for part in parts:
        if part in {item.rstrip() for item in SUB_BREAKS}:
            text.append(part + " " + random.choice(SMALL))
        else:
            text.append(part)
    return maybe_case(" ".join(text))


def capitalization():
    parts = words(random.randint(3, 6))
    style = random.randrange(4)
    if style == 0:
        body = " ".join(part.upper() for part in parts)
    elif style == 1:
        body = " ".join(parts)
        body = random.choice(INTERNAL_CAPS) + " " + body
    elif style == 2:
        body = " ".join([random.choice(HONORIFICS), word(), random.choice(HONORIFICS)])
    else:
        quote = random.choice(QUOTES)
        body = quote + " ".join(parts) + quote
    return body


def punctuation():
    left, mid, right = words(3)
    small = random.choice(SMALL)
    form = random.randrange(5)
    if form == 0:
        quote = random.choice(("'", "‘", "“"))
        return f"{quote}{small} {left}, {mid} {small}{random.choice(('.', '?', '!'))}"
    if form == 1:
        return f"{left}{random.choice(SUB_BREAKS)}{small} {right}"
    if form == 2:
        return f"{left}, {mid} and {right}"
    if form == 3:
        return f"({left}) {small} {right}."
    return f"{left}... {small} {right}?"


def apostrophes():
    token = (
        random.choice(APOS_PREFIXES)
        + random.choice(("'", "‘"))
        + random.choice(APOS_STEMS)
    )
    if random.random() < 0.35:
        token += random.choice(("'s", "s'", "ss"))
    return maybe_case(f"{token} {word()} {random.choice(SMALL)} {word()}")


def mc_prefixes():
    token = random.choice(MC_PREFIXES) + random.choice(MC_REST)
    if random.random() < 0.4:
        token = token + "-" + random.choice(MC_PREFIXES) + random.choice(MC_REST)
    return maybe_case(f"{word()} {token} {random.choice(SMALL)} {word()}")


def initials():
    letters = [random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ") for _ in range(random.randint(2, 4))]
    form = random.randrange(3)
    if form == 0:
        piece = ".".join(letters) + "."
    elif form == 1:
        piece = ".".join(letters)
    else:
        piece = letters[0] + "." + letters[1] + "."
    body = f"{word()} {piece} {random.choice(SMALL)} {word()}"
    if random.random() < 0.75:
        return body.upper()
    return body


def acronyms():
    acronym = random.choice(ACRONYMS)
    shown = random.choice((acronym, acronym.upper(), acronym.capitalize()))
    return f"{word()} with {shown} {random.choice(SMALL)} {word()}"


def hyphens():
    first, second, third = words(3)
    small = random.choice(SMALL)
    form = random.randrange(4)
    if form == 0:
        text = f"{first}-{small}-{second}"
    elif form == 1:
        text = f"{first}-{second}-{third}"
    elif form == 2:
        text = f"{first}-of-the-{second}"
    else:
        text = f"end-to-end {first}"
    return maybe_case(text)


def slashes():
    first, second, third = words(3)
    form = random.randrange(4)
    if form == 0:
        text = f"{first}/{second}"
    elif form == 1:
        text = f"{first}/{random.choice(SMALL)}/{second}"
    elif form == 2:
        text = f"and/or {first}"
    else:
        text = f"http://{first}"
    return maybe_case(text + f" {third}")


def whitespace():
    first, second, third = words(3)
    sep = random.choice(SPACES)
    lead = random.choice(("", " ", "\t", "\u00a0"))
    trail = random.choice(("", " ", "\t"))
    return f"{lead}{first}{sep}{second}{sep}{third}{trail}"


def dotted():
    host = word()
    tld = random.choice(("com", "org", "net", "io", "edu"))
    form = random.randrange(4)
    if form == 0:
        return f"visit http://{host}.{tld} for the {word()}"
    if form == 1:
        return f"see https://{host}.{tld}/{word()} now"
    if form == 2:
        return f"www.{host}.{tld} {random.choice(SMALL)} {word()}"
    return f"{host}.{tld}"


GENERATORS = (
    ordinary,
    small_words,
    capitalization,
    punctuation,
    apostrophes,
    mc_prefixes,
    initials,
    acronyms,
    hyphens,
    slashes,
    whitespace,
    dotted,
)


def valid_title(text):
    return bool(text) and not has_line_break(text) and text.splitlines() == [text]


def build_inputs():
    random.seed(1)
    practice = []
    hidden = []
    used = set()

    def add(title):
        if not valid_title(title) or title in used:
            return False
        used.add(title)
        if len(practice) < 2000:
            practice.append(title)
        else:
            hidden.append(title)
        return True

    for title in REQUIRED:
        if not add(title):
            raise SystemExit(f"Required practice title was rejected: {title!r}")
    for title in NOTES_CASES:
        add(title)

    guard = 0
    while len(hidden) < 2000:
        generated = GENERATORS[guard % len(GENERATORS)]()
        guard += 1
        add(generated)
        if guard > 200000:
            raise SystemExit(
                f"Stopped after {guard} attempts with "
                f"{len(practice)} practice and {len(hidden)} hidden titles."
            )

    if len(practice) != 2000 or len(hidden) != 2000:
        raise SystemExit(
            f"Expected 2000 + 2000 titles, got {len(practice)} and {len(hidden)}."
        )
    if len(set(practice)) != 2000 or len(set(hidden)) != 2000:
        raise SystemExit("Generated titles are not unique within a set.")
    if set(practice) & set(hidden):
        raise SystemExit("Practice and hidden titles overlap.")
    return practice, hidden


def write_records(path, records):
    if len(records) != 2000:
        raise SystemExit(f"{path.name} should contain 2000 records, not {len(records)}.")
    for record in records:
        if has_line_break(record) or record.splitlines() != [record]:
            raise SystemExit(f"{path.name} contains an embedded line break: {record!r}")
    text = "\n".join(records) + "\n"
    path.write_text(text, encoding="utf-8", newline="\n")


def read_records(path):
    raw = path.read_bytes()
    if b"\r" in raw:
        raise SystemExit(f"{path} contains CR bytes; line endings must be LF.")
    text = raw.decode("utf-8")
    if not text.endswith("\n"):
        raise SystemExit(f"{path} must end with an LF.")
    records = text[:-1].split("\n")
    if len(records) != 2000:
        raise SystemExit(f"{path} has {len(records)} records, expected 2000.")
    for record in records:
        if has_line_break(record) or record.splitlines() != [record]:
            raise SystemExit(f"{path} contains an embedded line break: {record!r}")
    return records


def main():
    titlecase_mod = load_titlecase()
    source = Path(titlecase_mod.__file__).resolve()
    practice, hidden = build_inputs()
    practice_expected = [titlecase_mod.titlecase(title) for title in practice]
    hidden_expected = [titlecase_mod.titlecase(title) for title in hidden]

    DATA.mkdir(parents=True, exist_ok=True)
    files = {
        DATA / "inputs.txt": practice,
        DATA / "hidden_inputs.txt": hidden,
        DATA / "expected.txt": practice_expected,
        DATA / "hidden_expected.txt": hidden_expected,
    }
    for path, records in files.items():
        write_records(path, records)
    loaded = {path.name: read_records(path) for path in files}
    if loaded["inputs.txt"] != practice or loaded["expected.txt"] != practice_expected:
        raise SystemExit("Practice files did not round-trip.")
    if loaded["hidden_inputs.txt"] != hidden or loaded["hidden_expected.txt"] != hidden_expected:
        raise SystemExit("Hidden files did not round-trip.")

    print(f"source={source}")
    print(f"REGEX_AVAILABLE={titlecase_mod.REGEX_AVAILABLE}")
    for name, records in loaded.items():
        print(f"{name}={len(records)}")
    print(f"practice_unique={len(set(practice)) == 2000}")
    print(f"hidden_unique={len(set(hidden)) == 2000}")
    print(f"disjoint={set(practice).isdisjoint(hidden)}")


if __name__ == "__main__":
    main()
