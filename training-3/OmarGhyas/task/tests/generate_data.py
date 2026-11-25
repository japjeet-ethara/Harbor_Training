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
if not SIBLING_ROOT.exists():
    alt = (TASK_ROOT.parent / "attack" / "target" / "environment" / "python-titlecase").resolve()
    if alt.exists():
        SIBLING_ROOT = alt
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
CONSONANT_ACRONYMS = (
    "html", "xml", "http", "cwm", "tcp", "udp", "rss", "sql", "css",
    "ssl", "ttl", "mhz", "phd",
)
GENERAL_ACRONYMS = ("cnn", "usa", "ibm", "nasa", "faq", "api", "gpu")
ALL_ACRONYMS = CONSONANT_ACRONYMS + GENERAL_ACRONYMS

MIXED = (
    "iTunes", "iPhone", "iOS", "eBay", "YouTube", "MacDonalds", "PPPoE",
    "IoT", "PhD", "XMLHttpRequest", "AT&T", "Q&A",
)
MC_STEMS = ("mcdonald", "mctavish", "mcclelland", "mcneil", "mcbrien")

UNICODE_WORDS = (
    "niño", "café", "naïve", "über", "façade", "résumé", "año", "señor",
    "ñandú", "βήτα", "σοφος", "ßeta", "ﬁle", "İstanbul", "東京",
    "Москва", "øl", "ægir", "élève", "crème", "brûlée",
)
HONORIFICS = ("mr", "mrs", "ms", "dr")
PUNCT_PREFIXES = ("", "\"", "'", "“", "‘", "(", "[", "_")
PUNCT_SUFFIXES = ("", ".", ",", "!", "?", ")", "]", "'", "\"", "”")
SUBPHRASES = (": ", "; ", "? ", "! ", ". ", " - ", " — ", " – ")
SPACES = (" ", "  ", "   ", "\t", "\t\t", " \t ", "\u00a0", "\u2002", "\u2003", "\u2009", "\u3000")
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
    kind = rng.randrange(3)
    if kind == 0:
        return word.lower()
    if kind == 1:
        return word[:1].upper() + word[1:].lower()
    return word.upper()


def join_words(rng: random.Random, tokens: list[str], spaces: tuple[str, ...] = (" ",)) -> str:
    if not tokens:
        return ""
    parts = [tokens[0]]
    for token in tokens[1:]:
        parts.append(pick(rng, spaces))
        parts.append(token)
    return "".join(parts)


def ordinary_case(rng: random.Random) -> str:
    count = rng.randint(2, 5)
    tokens = [cased(rng, pick(rng, ORDINARY)) for _ in range(count)]
    roll = rng.randrange(3)
    if roll == 0:
        pos = rng.randint(1, len(tokens) - 1)
        return join_words(rng, tokens[:pos]) + pick(rng, SUBPHRASES) + pick(rng, SMALL) + " " + join_words(rng, tokens[pos:])
    elif roll == 1:
        tokens.insert(rng.randrange(len(tokens) + 1), pick(rng, ORDINARY) + "-" + pick(rng, ORDINARY))
        return join_words(rng, tokens)
    else:
        tokens.insert(rng.randrange(len(tokens) + 1), pick(rng, ORDINARY) + "/" + pick(rng, ORDINARY))
        return join_words(rng, tokens)


def small_case(rng: random.Random) -> str:
    roll = rng.randrange(3)
    if roll == 0:
        head = [cased(rng, pick(rng, ORDINARY)), pick(rng, SMALL), cased(rng, pick(rng, ORDINARY))]
        tail = [pick(rng, SMALL), cased(rng, pick(rng, ORDINARY))]
        return join_words(rng, head) + pick(rng, SUBPHRASES) + join_words(rng, tail)
    elif roll == 1:
        hyphen_token = rng.choice(["step-by-step", "in-and-out", "state-of-the-art", "day-to-day", "apple-and-orange", "back-to-back", "wall-to-wall"])
        tokens = [cased(rng, pick(rng, ORDINARY)), hyphen_token, cased(rng, pick(rng, ORDINARY))]
        return join_words(rng, tokens)
    else:
        slash_token = rng.choice(["and/or", "in/out", "on/off", "to/from", "up/down"])
        tokens = [cased(rng, pick(rng, ORDINARY)), slash_token, cased(rng, pick(rng, ORDINARY))]
        return join_words(rng, tokens)


def punctuation_case(rng: random.Random) -> str:
    left = [pick(rng, PUNCT_PREFIXES) + cased(rng, pick(rng, ORDINARY))]
    right = [cased(rng, pick(rng, ORDINARY)) + pick(rng, PUNCT_SUFFIXES)]
    sub = pick(rng, SUBPHRASES)
    tail = pick(rng, SMALL) + " " + join_words(rng, right)
    return join_words(rng, left) + sub + tail


def hyphens_case(rng: random.Random) -> str:
    kind = rng.randrange(3)
    if kind == 0:
        token = "-".join(cased(rng, pick(rng, ORDINARY)) for _ in range(rng.randint(2, 3)))
    elif kind == 1:
        token = rng.choice(["step-by-step", "in-and-out", "state-of-the-art", "day-to-day", "out-of-office"])
    else:
        token = pick(rng, ORDINARY) + "/" + pick(rng, ORDINARY)
    extras = [cased(rng, pick(rng, ORDINARY)) for _ in range(rng.randint(1, 3))]
    pos = rng.randrange(len(extras) + 1)
    tokens = extras[:pos] + [token] + extras[pos:]
    return join_words(rng, tokens)


def apostrophes_case(rng: random.Random) -> str:
    if rng.randrange(2) == 0:
        stem = pick(rng, APOS_STEMS)
        mark = rng.choice(("'", "‘"))
        prefix = rng.choice(("o", "d", "l", "O", "D", "L"))
        token = f"{prefix}{mark}{stem.lower()}"
    else:
        token = pick(rng, MC_STEMS)
    tokens = [cased(rng, pick(rng, ORDINARY)) for _ in range(rng.randint(1, 3))]
    tokens.insert(rng.randrange(len(tokens) + 1), token)
    return join_words(rng, tokens)


def acronyms_case(rng: random.Random) -> str:
    roll = rng.randrange(2)
    if roll == 0:
        ac = pick(rng, CONSONANT_ACRONYMS).lower()
        tokens = [cased(rng, pick(rng, ORDINARY)) for _ in range(rng.randint(2, 4))]
        tokens.insert(rng.randrange(len(tokens) + 1), ac)
        return join_words(rng, tokens)
    else:
        tokens = [pick(rng, ORDINARY), pick(rng, SMALL), pick(rng, ALL_ACRONYMS), pick(rng, ORDINARY)]
        return join_words(rng, tokens).upper()


def mixed_case(rng: random.Random) -> str:
    token = rng.choice(("iTunes", "iPhone", "iOS", "eBay", "mcdonald", "mctavish", "mcclelland", "mcneil"))
    tokens = [cased(rng, pick(rng, ORDINARY)) for _ in range(rng.randint(1, 3))]
    tokens.insert(rng.randrange(len(tokens) + 1), token)
    return join_words(rng, tokens)


def whitespace_case(rng: random.Random) -> str:
    roll = rng.randrange(3)
    if roll == 0:
        head = [cased(rng, pick(rng, ORDINARY))]
        tail = [pick(rng, SMALL), cased(rng, pick(rng, ORDINARY))]
        text = join_words(rng, head, SPACES) + pick(rng, SUBPHRASES) + join_words(rng, tail, SPACES)
    elif roll == 1:
        tokens = [cased(rng, pick(rng, ORDINARY)), pick(rng, ("apple-bridge", "step-by-step", "and/or")), cased(rng, pick(rng, ORDINARY))]
        text = join_words(rng, tokens, SPACES)
    else:
        tokens = [cased(rng, pick(rng, ORDINARY)), pick(rng, CONSONANT_ACRONYMS).lower(), cased(rng, pick(rng, ORDINARY))]
        text = join_words(rng, tokens, SPACES)
    return text


def all_caps_case(rng: random.Random) -> str:
    tokens = [pick(rng, ORDINARY), pick(rng, SMALL), pick(rng, ORDINARY)]
    if rng.randrange(2) == 0:
        tokens.append(pick(rng, ORDINARY))
    return join_words(rng, tokens).upper()


def unicode_case(rng: random.Random) -> str:
    roll = rng.randrange(3)
    if roll == 0:
        uword = pick(rng, ("ßeta", "ﬁle", "élève", "café", "brûlée", "naïve"))
        tokens = [cased(rng, pick(rng, ORDINARY)), uword, cased(rng, pick(rng, ORDINARY))]
        return join_words(rng, tokens)
    elif roll == 1:
        uword = pick(rng, UNICODE_WORDS)
        return cased(rng, uword) + pick(rng, SUBPHRASES) + pick(rng, SMALL) + " " + cased(rng, pick(rng, ORDINARY))
    else:
        tokens = [pick(rng, UNICODE_WORDS), pick(rng, SMALL), pick(rng, UNICODE_WORDS)]
        return join_words(rng, tokens).upper()


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


def generate_inputs(rng: random.Random, blocked: set[str], titlecase) -> list[str]:
    if CASE_COUNT % len(CATEGORIES) != 0:
        raise RuntimeError("case count must divide evenly across categories")
    per_category = CASE_COUNT // len(CATEGORIES)
    chosen: list[str] = []
    seen = set(blocked)
    for category in CATEGORIES:
        builder = BUILDERS[category]
        produced = 0
        attempts = 0
        limit = per_category * 200
        while produced < per_category:
            attempts += 1
            if attempts > limit:
                raise RuntimeError(f"could not fill category {category} after {attempts} attempts")
            text = builder(rng)
            if not one_line(text) or text in seen:
                continue
            expected = titlecase(text)
            if expected == text:
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
        if expected == text:
            raise RuntimeError(f"fixed point generated: {text}")
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
        if record["input"] == record["expected"]:
            raise RuntimeError(f"{path} contains fixed point: {record['input']}")
        actual = titlecase(record["input"])
        if actual != record["expected"]:
            raise RuntimeError(f"{path} expected value does not match titlecase()")
    return set(inputs)


def main() -> None:
    titlecase, titlecase_mod, regex = load_reference()
    visible_rng, hidden_rng = separate_streams()
    visible_inputs = generate_inputs(visible_rng, blocked=set(), titlecase=titlecase)
    hidden_inputs = generate_inputs(hidden_rng, blocked=set(visible_inputs), titlecase=titlecase)
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
