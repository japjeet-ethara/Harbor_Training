"""Deterministic visible and hidden datasets for the titlecase task.

Expected strings come from the sibling repository's titlecase() with the
third-party regex engine. This script stays in tests/ and is not part of
the Go program.
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

CASE_COUNT = 2000
SEED = 1

TASK_ROOT = Path(__file__).resolve().parents[1]
SIBLING_ROOT = (TASK_ROOT.parent / "python-titlecase").resolve()
EXPECTED_MODULE = (SIBLING_ROOT / "titlecase" / "__init__.py").resolve()
DATA_DIR = Path(__file__).resolve().parent / "data"
VISIBLE_PATH = DATA_DIR / "visible.jsonl"
HIDDEN_PATH = DATA_DIR / "hidden.jsonl"

ORDINARY = (
    "apple", "bridge", "camera", "delta", "engine", "forest", "garden",
    "harbor", "island", "journal", "kernel", "lantern", "market", "notebook",
    "orange", "paper", "quartz", "river", "signal", "timber", "umbrella",
    "valley", "window", "yellow", "zebra", "copper", "silver", "marble",
    "velvet", "crystal", "morning", "evening", "station", "library",
    "captain", "soldier", "village", "mountain", "ocean", "planet",
    "rocket", "studio", "theater", "gallery", "factory", "meadow",
    "letter", "parcel", "compass", "harvest",
)
SMALL = (
    "a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in",
    "of", "on", "or", "the", "to", "v", "v.", "via", "vs", "vs.",
)
APOS_STEMS = (
    "reilly", "connor", "brien", "malley", "grange", "oreal", "artagnan",
    "arcy", "angelo", "clock", "neil", "keefe", "donnell", "sullivan",
)
ACRONYMS = (
    "cnn", "html", "xml", "http", "phd", "www", "cwm", "tcp", "udp",
    "fyi", "usa", "ibm", "nasa", "faq", "rss", "sql", "css", "api",
    "gpu", "ssl", "ttl", "mhz",
)
MIXED = (
    "iTunes", "iPhone", "iOS", "eBay", "YouTube", "MacDonalds", "PPPoE",
    "IoT", "PhD", "XMLHttpRequest", "AT&T", "Q&A", "McDonald", "McTavish",
    "IOs", "newYork",
)
UNICODE_WORDS = (
    "niño", "café", "naïve", "über", "façade", "résumé", "año", "señor",
    "ñandú", "βήτα", "σοφος", "ΣΟΦΟΣ", "ßeta", "ﬁle", "İstanbul", "東京",
    "Москва", "øl", "ægir", "Ñoño", "élève", "crème", "brûlée",
)
HONORIFICS = ("mr", "mrs", "ms", "dr", "Mr", "MRS", "Dr")
PUNCT_PREFIXES = ("", "\"", "'", "“", "‘", "(", "[", "_", "...", "”")
PUNCT_SUFFIXES = ("", ".", ",", "!", "?", ":", ";", ")", "]", "'", "\"", "”")
SUBPHRASES = (": ", "; ", "? ", "! ", ". ", " - ", " — ", " – ", " — ")
SPACES = (" ", "  ", "   ", "\t", "\t\t", " \t ", "\u00a0", "\u2002", "\u2003", "\u2009", "\u3000")
HYPHEN_SMALL = ("in", "of", "the", "and", "to", "by", "a", "or")
CATEGORIES = (
    "ordinary",
    "small",
    "punctuation",
    "hyphens",
    "apostrophes",
    "acronyms",
    "mixed",
    "whitespace",
    "all_caps",
    "unicode",
)


def separate_streams() -> tuple[random.Random, random.Random]:
    """Two independent streams, both determined by random.seed(1)."""
    random.seed(SEED)
    visible_rng = random.Random(random.getrandbits(128))
    hidden_rng = random.Random(random.getrandbits(128))
    return visible_rng, hidden_rng


def load_reference():
    try:
        import regex
    except ImportError as exc:
        raise SystemExit("third-party regex module is not available") from exc

    if not EXPECTED_MODULE.is_file():
        raise SystemExit(f"sibling titlecase module not found: {EXPECTED_MODULE}")

    sys.path.insert(0, str(SIBLING_ROOT))
    import titlecase as titlecase_mod

    origin = Path(titlecase_mod.__file__).resolve()
    if origin != EXPECTED_MODULE:
        raise SystemExit(
            f"imported titlecase from {origin}, expected {EXPECTED_MODULE}"
        )
    if not getattr(titlecase_mod, "REGEX_AVAILABLE", False):
        raise SystemExit("titlecase is using the re fallback instead of regex")
    if not hasattr(regex, "compile") or Path(regex.__file__).name == "re.py":
        raise SystemExit(f"unexpected regex module: {regex.__file__}")
    return titlecase_mod.titlecase, titlecase_mod, regex


def pick(rng: random.Random, pool: tuple[str, ...]) -> str:
    return rng.choice(pool)


def cased(rng: random.Random, word: str) -> str:
    kind = rng.randrange(4)
    if kind == 0:
        return word.lower()
    if kind == 1:
        return word[:1].upper() + word[1:]
    if kind == 2:
        return word.upper()
    return word


def join_words(rng: random.Random, tokens: list[str], spaces: tuple[str, ...] = (" ",)) -> str:
    if not tokens:
        return ""
    parts = [tokens[0]]
    for token in tokens[1:]:
        parts.append(pick(rng, spaces))
        parts.append(token)
    return "".join(parts)


def ordinary_case(rng: random.Random) -> str:
    count = rng.randint(2, 6)
    tokens = [cased(rng, pick(rng, ORDINARY)) for _ in range(count)]
    if rng.randrange(5) == 0:
        tokens.insert(rng.randrange(len(tokens) + 1), pick(rng, HONORIFICS))
    return join_words(rng, tokens)


def small_case(rng: random.Random) -> str:
    tokens = [pick(rng, SMALL), cased(rng, pick(rng, ORDINARY))]
    for _ in range(rng.randint(1, 4)):
        tokens.append(pick(rng, SMALL))
        tokens.append(cased(rng, pick(rng, ORDINARY)))
    tokens.append(pick(rng, SMALL))
    if rng.randrange(2) == 0:
        tokens[0] = pick(rng, SMALL)
    return join_words(rng, tokens)


def punctuation_case(rng: random.Random) -> str:
    left = [pick(rng, PUNCT_PREFIXES) + cased(rng, pick(rng, ORDINARY)) + pick(rng, PUNCT_SUFFIXES)]
    right_count = rng.randint(1, 4)
    right = [
        pick(rng, PUNCT_PREFIXES) + cased(rng, pick(rng, ORDINARY)) + pick(rng, PUNCT_SUFFIXES)
        for _ in range(right_count)
    ]
    phrase = join_words(rng, left + right)
    if rng.randrange(2) == 0:
        cut = rng.randint(0, len(right))
        head = join_words(rng, left + right[:cut])
        tail = join_words(rng, right[cut:] or [cased(rng, pick(rng, SMALL))])
        phrase = head + pick(rng, SUBPHRASES) + tail
    if rng.randrange(4) == 0:
        phrase += " " + pick(rng, ("example.com", "del.icio.us", "http://foo.com", "a.m.", "Ph.D."))
    return phrase


def hyphens_case(rng: random.Random) -> str:
    kind = rng.randrange(4)
    if kind == 0:
        token = "-".join(cased(rng, pick(rng, ORDINARY)) for _ in range(rng.randint(2, 4)))
    elif kind == 1:
        token = "-".join(
            [
                cased(rng, pick(rng, ORDINARY)),
                pick(rng, HYPHEN_SMALL),
                pick(rng, HYPHEN_SMALL),
                cased(rng, pick(rng, ORDINARY)),
            ]
        )
    elif kind == 2:
        token = cased(rng, pick(rng, ORDINARY)) + rng.choice(("-", "--", "-")) + cased(rng, pick(rng, ORDINARY))
    else:
        token = "/".join(cased(rng, pick(rng, ORDINARY)) for _ in range(rng.randint(2, 3)))
    extras = [cased(rng, pick(rng, ORDINARY)) for _ in range(rng.randint(0, 3))]
    position = rng.randrange(len(extras) + 1)
    tokens = extras[:position] + [token] + extras[position:]
    return join_words(rng, tokens)


def apostrophes_case(rng: random.Random) -> str:
    letter = rng.choice(("o", "O", "l", "L", "d", "D"))
    mark = rng.choice(("'", "‘"))
    stem = pick(rng, APOS_STEMS)
    stem_case = rng.randrange(3)
    if stem_case == 1:
        stem = stem.upper()
    elif stem_case == 2:
        stem = stem[:1].upper() + stem[1:]
    token = f"{letter}{mark}{stem}"
    if rng.randrange(4) == 0:
        token += rng.choice(("'s", "’s", "'"))
    tokens = [cased(rng, pick(rng, ORDINARY)) for _ in range(rng.randint(0, 3))]
    tokens.insert(rng.randrange(len(tokens) + 1), token)
    if rng.randrange(3) == 0:
        tokens.append(rng.choice(("it's", "don't", "can't", "y'all", "o'clock")))
    return join_words(rng, tokens)


def acronyms_case(rng: random.Random) -> str:
    tokens = []
    for _ in range(rng.randint(3, 7)):
        if rng.randrange(2) == 0:
            word = pick(rng, ACRONYMS)
            tokens.append(word.upper() if rng.randrange(2) == 0 else word.lower())
        else:
            tokens.append(cased(rng, pick(rng, ORDINARY)))
    if not any(token.lower().strip(".") in {item.lower() for item in ACRONYMS} for token in tokens):
        tokens.insert(rng.randrange(len(tokens) + 1), pick(rng, ACRONYMS))
    return join_words(rng, tokens)


def mixed_case(rng: random.Random) -> str:
    tokens = [pick(rng, MIXED)]
    for _ in range(rng.randint(1, 4)):
        tokens.append(cased(rng, pick(rng, ORDINARY)) if rng.randrange(3) else pick(rng, SMALL))
    rng.shuffle(tokens)
    if rng.randrange(3) == 0:
        prefix = rng.choice(("mc", "Mc", "MC"))
        tokens.append(prefix + pick(rng, ("tavish", "donald", "clelland", "foo", "bar", "by")))
    return join_words(rng, tokens)


def whitespace_case(rng: random.Random) -> str:
    tokens = [cased(rng, pick(rng, ORDINARY)) for _ in range(rng.randint(2, 5))]
    if rng.randrange(2) == 0:
        tokens.insert(rng.randrange(len(tokens)), pick(rng, SMALL))
    text = join_words(rng, tokens, SPACES)
    if rng.randrange(2) == 0:
        text = pick(rng, SPACES) + text
    if rng.randrange(2) == 0:
        text = text + pick(rng, SPACES)
    return text


def all_caps_case(rng: random.Random) -> str:
    tokens = []
    for _ in range(rng.randint(2, 7)):
        pool = ORDINARY if rng.randrange(3) else SMALL
        tokens.append(pick(rng, pool))
    if rng.randrange(2) == 0:
        tokens.append(pick(rng, ACRONYMS))
    text = join_words(rng, tokens).upper()
    if rng.randrange(4) == 0:
        text = text.replace(" ", rng.choice(("  ", "\t")), 1)
    return text


def unicode_case(rng: random.Random) -> str:
    tokens = [pick(rng, UNICODE_WORDS)]
    for _ in range(rng.randint(1, 4)):
        tokens.append(pick(rng, UNICODE_WORDS) if rng.randrange(2) == 0 else cased(rng, pick(rng, ORDINARY)))
    rng.shuffle(tokens)
    text = join_words(rng, tokens, (" ", " ", "\u00a0"))
    if rng.randrange(3) == 0:
        text = pick(rng, ("“", "‘", "¿", "«")) + text + pick(rng, ("”", "’", "?", "»"))
    return text


BUILDERS = {
    "ordinary": ordinary_case,
    "small": small_case,
    "punctuation": punctuation_case,
    "hyphens": hyphens_case,
    "apostrophes": apostrophes_case,
    "acronyms": acronyms_case,
    "mixed": mixed_case,
    "whitespace": whitespace_case,
    "all_caps": all_caps_case,
    "unicode": unicode_case,
}


def one_line(text: str) -> bool:
    return "\n" not in text and "\r" not in text and "\u2028" not in text and "\u2029" not in text


def generate_inputs(rng: random.Random, blocked: set[str]) -> list[str]:
    if CASE_COUNT % len(CATEGORIES) != 0:
        raise RuntimeError("case count must divide evenly across categories")
    per_category = CASE_COUNT // len(CATEGORIES)
    chosen: list[str] = []
    seen = set(blocked)
    for category in CATEGORIES:
        builder = BUILDERS[category]
        produced = 0
        attempts = 0
        limit = per_category * 100
        while produced < per_category:
            attempts += 1
            if attempts > limit:
                raise RuntimeError(f"could not fill category {category} after {attempts} attempts")
            text = builder(rng)
            if not one_line(text) or text in seen:
                continue
            seen.add(text)
            chosen.append(text)
            produced += 1
    if len(chosen) != CASE_COUNT or len(set(chosen)) != CASE_COUNT:
        raise RuntimeError("generated input count is not the required unique size")
    return chosen


def records_for(titlecase, inputs: list[str]) -> list[dict[str, str]]:
    records = []
    for text in inputs:
        expected = titlecase(text)
        if not isinstance(expected, str):
            raise RuntimeError(f"titlecase returned {type(expected).__name__}, expected str")
        records.append({"input": text, "expected": expected})
    return records


def write_jsonl(path: Path, records: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def read_jsonl(path: Path) -> list[dict[str, str]]:
    records = []
    with path.open(encoding="utf-8", newline="\n") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.endswith("\n"):
                raise RuntimeError(f"{path} line {line_number} is missing a newline")
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"{path} line {line_number} is not valid JSON") from exc
            if not isinstance(record, dict) or set(record) != {"input", "expected"}:
                raise RuntimeError(f"{path} line {line_number} must contain only input and expected")
            if not isinstance(record["input"], str) or not isinstance(record["expected"], str):
                raise RuntimeError(f"{path} line {line_number} fields must be strings")
            records.append(record)
    return records


def validate(titlecase, path: Path, records: list[dict[str, str]]) -> set[str]:
    loaded = read_jsonl(path)
    if loaded != records:
        raise RuntimeError(f"{path} did not round-trip")
    if len(loaded) != CASE_COUNT:
        raise RuntimeError(f"{path} has {len(loaded)} records, expected {CASE_COUNT}")
    inputs = [record["input"] for record in loaded]
    if len(set(inputs)) != CASE_COUNT:
        raise RuntimeError(f"{path} inputs are not unique")
    for record in loaded:
        actual = titlecase(record["input"])
        if actual != record["expected"]:
            raise RuntimeError(f"{path} expected value does not match titlecase()")
    return set(inputs)


def main() -> None:
    titlecase, titlecase_mod, regex = load_reference()
    visible_rng, hidden_rng = separate_streams()
    visible_inputs = generate_inputs(visible_rng, blocked=set())
    hidden_inputs = generate_inputs(hidden_rng, blocked=set(visible_inputs))
    visible_records = records_for(titlecase, visible_inputs)
    hidden_records = records_for(titlecase, hidden_inputs)
    write_jsonl(VISIBLE_PATH, visible_records)
    write_jsonl(HIDDEN_PATH, hidden_records)
    visible_set = validate(titlecase, VISIBLE_PATH, visible_records)
    hidden_set = validate(titlecase, HIDDEN_PATH, hidden_records)
    if visible_set & hidden_set:
        raise RuntimeError("visible and hidden inputs overlap")
    print(f"visible_cases={len(visible_set)}")
    print(f"hidden_cases={len(hidden_set)}")
    print(f"reference_module={Path(titlecase_mod.__file__).resolve()}")
    print(f"regex_imported={regex.__file__}")
    print("validation=passed")


if __name__ == "__main__":
    main()
