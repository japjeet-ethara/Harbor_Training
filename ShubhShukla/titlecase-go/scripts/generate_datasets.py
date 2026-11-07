"""Generate deterministic titlecase datasets.

Each record is one title. Files are UTF-8 with a trailing LF after every
record, including empty titles. The line break is not part of the title.

Expected lines are produced by calling the original Python titlecase()
with its defaults. The third-party regex package is blocked so the run
matches the stdlib re path documented in NOTES.md.

Usage:
    python scripts/generate_datasets.py
    python scripts/generate_datasets.py --check
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from pathlib import Path


TASK_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = TASK_ROOT.parent
PY_SRC = REPO_ROOT / "python-titlecase"
DATA_DIR = TASK_ROOT / "tests" / "datasets"

VISIBLE_INPUT = DATA_DIR / "visible_input.txt"
VISIBLE_EXPECTED = DATA_DIR / "visible_expected.txt"
HIDDEN_INPUT = DATA_DIR / "hidden_input.txt"
HIDDEN_EXPECTED = DATA_DIR / "hidden_expected.txt"
MANIFEST = DATA_DIR / "manifest.json"

COUNT = 2000
SEED = 1


class _BlockRegex:
    """Fail any import of the optional third-party regex package."""

    def find_spec(self, fullname, path, target=None):
        if fullname == "regex" or fullname.startswith("regex."):
            raise ImportError("regex blocked; NOTES.md uses the stdlib re path")
        return None


sys.meta_path.insert(0, _BlockRegex())
sys.path.insert(0, str(PY_SRC))

from titlecase import REGEX_AVAILABLE, titlecase  # noqa: E402
from titlecase.tests import TEST_DATA  # noqa: E402


SMALL = [
    "a",
    "an",
    "and",
    "as",
    "at",
    "but",
    "by",
    "en",
    "for",
    "if",
    "in",
    "of",
    "on",
    "or",
    "the",
    "to",
    "v",
    "v.",
    "via",
    "vs",
    "vs.",
]
CONTENT = [
    "apple",
    "author",
    "bridge",
    "camera",
    "capital",
    "castle",
    "dance",
    "editor",
    "family",
    "force",
    "garden",
    "harbor",
    "history",
    "island",
    "journey",
    "kingdom",
    "letter",
    "market",
    "moment",
    "music",
    "night",
    "office",
    "orange",
    "paper",
    "player",
    "public",
    "quest",
    "report",
    "river",
    "school",
    "silver",
    "spring",
    "summer",
    "system",
    "table",
    "umbrella",
    "valley",
    "window",
    "winter",
    "yellow",
    "zebra",
    "answer",
    "border",
    "captain",
    "diamond",
    "engine",
    "forest",
    "gallery",
    "horizon",
    "library",
    "machine",
    "network",
    "opinion",
    "planet",
    "quarter",
    "signal",
    "traffic",
    "village",
    "weather",
]
SURNAMES = [
    "smith",
    "jones",
    "garcia",
    "brown",
    "martin",
    "clark",
    "lewis",
    "walker",
    "young",
    "king",
    "wright",
    "lopez",
    "hill",
    "green",
    "adams",
    "baker",
]
UNICODE_WORDS = [
    "niño",
    "café",
    "naïve",
    "résumé",
    "ångström",
    "façade",
    "über",
    "señor",
    "crème",
    "brûlée",
    "él",
    "arrivé",
    "hier",
    "ýæ",
    "ñø",
    "año",
    "mañana",
    "él Niño",
]
BRANDS = [
    "iTunes",
    "iPhone",
    "macOS",
    "AT&T",
    "Q&A",
    "q&a",
    "PPPoE",
    "OmniFocus",
    "iÑunes",
    "MacDonalds",
]
INITIALS = [
    "D.C.",
    "A.B.",
    "A.B.C.",
    "A.B.C",
    "e.g.",
    "a.m.",
    "p.m.",
    "Ph.D.",
    "example.com",
    "del.icio.us",
    "item.one",
    "file_name.txt",
    "section.a",
    "U.S.",
    "U.S.A.",
]
ACRONYMS = [
    "cnn",
    "html",
    "css",
    "tcp",
    "ftp",
    "nfl",
    "ibm",
    "bbc",
    "udp",
    "nyc",
    "rhythm",
    "cry",
    "st",
    "bb",
    "bbb",
    "cns",
    "mss",
]
ORDINALS = ["1st", "2nd", "3rd", "4th", "5th", "34th", "2lmc", "123", "7", "5th st", "X ≤ 7"]
SUBPHRASE = [":", ";", "?", "!", ".", "-", "–", "‒", "—", "―"]
SPACES = [" ", "  ", "   ", "\t", "\u00a0", " \t "]
QUOTES = [("'", "'"), ('"', '"'), ("‘", "’"), ("“", "”")]

# Hidden and the random portion of visible both draw from these weights.
QUOTAS = {
    "simple": 180,
    "all_caps": 140,
    "small_edges": 120,
    "hyphen": 120,
    "slash": 100,
    "doubleslash": 60,
    "apostrophe": 120,
    "honorific": 80,
    "initials": 100,
    "brands": 80,
    "acronyms": 100,
    "unicode": 150,
    "subphrase": 150,
    "whitespace": 80,
    "digits": 70,
    "mc": 80,
    "quotes": 80,
    "mixed": 150,
    "short": 40,
}


def pick(pool: list[str]) -> str:
    return random.choice(pool)


def join_ws(parts: list[str]) -> str:
    if not parts:
        return ""
    out = [parts[0]]
    for part in parts[1:]:
        out.append(pick(SPACES))
        out.append(part)
    return "".join(out)


def content_word() -> str:
    roll = random.random()
    if roll < 0.25:
        return pick(SMALL)
    if roll < 0.32:
        return pick(ACRONYMS)
    return pick(CONTENT)


def sentence(n: int | None = None) -> str:
    count = n if n is not None else random.randint(3, 9)
    return join_ws([content_word() for _ in range(count)])


def apos_word() -> str:
    prefix = pick(["o", "O", "l", "L", "d", "D"])
    mark = pick(["'", "‘"])
    stem = pick(
        [
            "reilly",
            "brien",
            "clock",
            "grange",
            "amour",
            "artagnan",
            "angelo",
            "neil",
            "malley",
            "hare",
            "donnell",
        ]
    )
    word = prefix + mark + stem
    if random.random() < 0.35:
        word += pick(["'s", "’s"])
    if random.random() < 0.2 and len(word) > 3:
        word = word[:3] + word[3].upper() + word[4:]
    return word


def hyphen_token() -> str:
    count = random.randint(2, 4)
    parts = []
    for _ in range(count):
        if random.random() < 0.45:
            parts.append(pick(SMALL))
        else:
            parts.append(pick(CONTENT))
    return "-".join(parts)


def slash_token() -> str:
    def piece() -> str:
        if random.random() < 0.4:
            return pick(SMALL)
        return pick(CONTENT)

    parts = [piece(), piece()]
    if random.random() < 0.35:
        parts.append(piece())
    return "/".join(parts)


def mc_word() -> str:
    prefix = pick(["mc", "Mc", "MC"])
    stem = pick(
        ["donald", "tavish", "coy", "carthy", "mahon", "foo", "by", "but", "do", "clelland"]
    )
    word = prefix + stem
    if random.random() < 0.3:
        tail = pick(["bar", "mcbar", pick(SMALL), prefix + "bay"])
        word = word + "-" + tail
    return word


def make_simple() -> str:
    return sentence()


def make_all_caps() -> str:
    return sentence(random.randint(3, 8)).upper()


def make_small_edges() -> str:
    middle = [content_word() for _ in range(random.randint(2, 6))]
    return join_ws([pick(SMALL), *middle, pick(SMALL)])


def make_hyphen() -> str:
    return join_ws([content_word(), hyphen_token(), content_word()])


def make_slash() -> str:
    return join_ws([content_word(), slash_token(), content_word()])


def make_doubleslash() -> str:
    if random.random() < 0.5:
        host = pick(CONTENT)
        path = pick(CONTENT)
        token = f"http://{host}.com/{path}"
    else:
        token = f"{pick(CONTENT)}//{pick(CONTENT)}"
    return join_ws([pick(["see", "open", "visit", "check", "this"]), token, content_word()])


def make_apostrophe() -> str:
    return join_ws([content_word(), apos_word(), pick(SMALL), content_word()])


def make_honorific() -> str:
    title = pick(
        ["mr", "Mr", "MR", "mrs", "Mrs", "MRS", "ms", "Ms", "MS", "dr", "Dr", "DR", "mr.", "mrs.", "Mss", "mss"]
    )
    return join_ws([title, pick(SURNAMES), pick(SMALL), title, pick(CONTENT)])


def make_initials() -> str:
    return join_ws([content_word(), pick(INITIALS), pick(SMALL), content_word()])


def make_brands() -> str:
    return join_ws([content_word(), pick(BRANDS), pick(SMALL), content_word()])


def make_acronyms() -> str:
    token = pick(ACRONYMS)
    if random.random() < 0.5:
        token = token.upper()
    return join_ws([content_word(), pick(SMALL), token, content_word()])


def make_unicode() -> str:
    foreign = pick(UNICODE_WORDS)
    count = random.randint(3, 7)
    slot = random.randrange(count)
    parts = [foreign if i == slot else content_word() for i in range(count)]
    line = join_ws(parts)
    if random.random() < 0.35:
        line = line.upper()
    return line


def make_subphrase() -> str:
    left = sentence(random.randint(2, 5))
    right = join_ws([pick(SMALL), content_word(), content_word()])
    return f"{left}{pick(SUBPHRASE)} {right}"


def make_whitespace() -> str:
    if random.random() < 0.2:
        return pick([" ", "  ", "   ", "\t", "\t\t", " \t ", "\u00a0", "\u00a0\u00a0", "\u2009", "\u200a", "\u2006"])
    base = sentence(random.randint(2, 6))
    kind = random.randrange(5)
    if kind == 0:
        return "  " + base
    if kind == 1:
        return base + "   "
    if kind == 2:
        return "\t" + base + "\t"
    if kind == 3:
        return base.replace(" ", "\u00a0", 1)
    return " \t " + base + " \t "


def make_digits() -> str:
    return join_ws([content_word(), pick(ORDINALS), pick(SMALL), content_word()])


def make_mc() -> str:
    word = mc_word()
    if random.random() < 0.25:
        word = word.upper()
    return join_ws([pick(["mr", "the", content_word()]), word, pick(SMALL), content_word()])


def make_quotes() -> str:
    opening, closing = pick(QUOTES)
    inner = join_ws([pick(SMALL), content_word(), pick(SMALL)])
    quoted = f"{opening}{inner}{closing}"
    return join_ws([content_word(), quoted, content_word()])


def make_mixed() -> str:
    feature = pick(
        [
            hyphen_token(),
            slash_token(),
            apos_word(),
            pick(BRANDS),
            pick(ACRONYMS).upper(),
            pick(UNICODE_WORDS),
            mc_word(),
            pick(INITIALS),
        ]
    )
    line = join_ws([sentence(random.randint(2, 4)), feature, pick(SMALL), content_word()])
    if random.random() < 0.15:
        line = line.upper()
    return line


def make_short() -> str:
    kind = random.randrange(4)
    if kind == 0:
        return pick(SMALL)
    if kind == 1:
        return pick(CONTENT)
    if kind == 2:
        return pick(["?", "!", "...", "—", "–", "&"])
    return join_ws([pick(SMALL), pick(CONTENT)])


FACTORIES = {
    "simple": make_simple,
    "all_caps": make_all_caps,
    "small_edges": make_small_edges,
    "hyphen": make_hyphen,
    "slash": make_slash,
    "doubleslash": make_doubleslash,
    "apostrophe": make_apostrophe,
    "honorific": make_honorific,
    "initials": make_initials,
    "brands": make_brands,
    "acronyms": make_acronyms,
    "unicode": make_unicode,
    "subphrase": make_subphrase,
    "whitespace": make_whitespace,
    "digits": make_digits,
    "mc": make_mc,
    "quotes": make_quotes,
    "mixed": make_mixed,
    "short": make_short,
}


def canonical_inputs() -> list[str]:
    found = []
    seen: set[str] = set()
    for source, _expected in TEST_DATA:
        if "\n" in source or "\r" in source:
            continue
        if source in seen:
            continue
        seen.add(source)
        found.append(source)
    return found


def scale_quotas(total: int) -> dict[str, int]:
    full = sum(QUOTAS.values())
    if total == full:
        return dict(QUOTAS)
    raw = {name: quota * total / full for name, quota in QUOTAS.items()}
    floors = {name: int(value) for name, value in raw.items()}
    remainder = total - sum(floors.values())
    order = sorted(QUOTAS, key=lambda name: (raw[name] - floors[name], QUOTAS[name]), reverse=True)
    for name in order[:remainder]:
        floors[name] += 1
    return floors


def take_unique(factory, seen: set[str]) -> str:
    for _ in range(80):
        sample = factory()
        if "\n" in sample or "\r" in sample:
            continue
        if sample not in seen:
            seen.add(sample)
            return sample
    extra = pick(CONTENT)
    sample = factory() + " " + extra
    while sample in seen or "\n" in sample or "\r" in sample:
        sample = sample + " " + pick(CONTENT)
    seen.add(sample)
    return sample


def fill(count: int, seen: set[str]) -> tuple[list[str], dict[str, int]]:
    quotas = scale_quotas(count)
    lines: list[str] = []
    used = {name: 0 for name in QUOTAS}
    for name, quota in quotas.items():
        factory = FACTORIES[name]
        for _ in range(quota):
            lines.append(take_unique(factory, seen))
            used[name] += 1
    if len(lines) != count:
        raise RuntimeError(f"expected {count} generated lines, got {len(lines)}")
    return lines, used


def encode_lines(lines: list[str]) -> bytes:
    for line in lines:
        if "\n" in line or "\r" in line:
            raise ValueError("record contains a line break")
    return "".join(f"{line}\n" for line in lines).encode("utf-8")


def decode_lines(payload: bytes) -> list[str]:
    if payload.startswith(b"\xef\xbb\xbf"):
        raise ValueError("UTF-8 BOM is not allowed")
    text = payload.decode("utf-8")
    if not text.endswith("\n"):
        raise ValueError("dataset must end with LF")
    if "\r" in text:
        raise ValueError("dataset must not contain CR")
    parts = text.split("\n")
    if parts[-1] != "":
        raise ValueError("dataset must end with LF")
    return parts[:-1]


def expected_for(lines: list[str]) -> list[str]:
    outputs = []
    for line in lines:
        result = titlecase(line)
        if "\n" in result or "\r" in result:
            raise ValueError(f"titlecase introduced a line break for {line!r}")
        outputs.append(result)
    return outputs


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def build() -> dict:
    if REGEX_AVAILABLE:
        raise RuntimeError("third-party regex package is active; refuse to generate")
    if sum(QUOTAS.values()) != COUNT:
        raise RuntimeError("category quotas must sum to 2000")

    random.seed(SEED)
    seen: set[str] = set()
    visible = []
    for source in canonical_inputs():
        if source in seen:
            continue
        seen.add(source)
        visible.append(source)
    if "" not in seen:
        seen.add("")
        visible.append("")

    random_visible, visible_counts = fill(COUNT - len(visible), seen)
    visible.extend(random_visible)
    hidden, hidden_counts = fill(COUNT, seen)

    if len(visible) != COUNT or len(hidden) != COUNT:
        raise RuntimeError("dataset size mismatch")
    if set(visible) & set(hidden):
        raise RuntimeError("visible and hidden inputs overlap")
    if len(set(visible)) != COUNT or len(set(hidden)) != COUNT:
        raise RuntimeError("duplicate input inside a dataset")

    for source, expected in TEST_DATA:
        if "\n" in source or "\r" in source:
            continue
        if titlecase(source) != expected:
            raise RuntimeError(f"library mismatch on canonical input {source!r}")

    visible_expected = expected_for(visible)
    hidden_expected = expected_for(hidden)
    return {
        "visible_input": visible,
        "visible_expected": visible_expected,
        "hidden_input": hidden,
        "hidden_expected": hidden_expected,
        "visible_counts": visible_counts,
        "hidden_counts": hidden_counts,
        "canonical_count": len(visible) - len(random_visible),
    }


def write_datasets(built: dict) -> dict[str, dict[str, int | str]]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    files = {
        "visible_input.txt": encode_lines(built["visible_input"]),
        "visible_expected.txt": encode_lines(built["visible_expected"]),
        "hidden_input.txt": encode_lines(built["hidden_input"]),
        "hidden_expected.txt": encode_lines(built["hidden_expected"]),
    }
    info = {}
    for name, payload in files.items():
        path = DATA_DIR / name
        path.write_bytes(payload)
        info[name] = {"bytes": len(payload), "sha256": sha256(payload)}
    manifest = {
        "seed": SEED,
        "encoding": "utf-8",
        "record_separator": "\n",
        "record_separator_is_not_part_of_title": True,
        "titlecase_defaults": {
            "callback": None,
            "small_first_last": True,
            "preserve_blank_lines": False,
            "normalise_space_characters": False,
        },
        "regex_available": False,
        "titlecase_version": __import__("titlecase").__version__,
        "python": sys.version,
        "visible_count": COUNT,
        "hidden_count": COUNT,
        "canonical_single_line_inputs_in_visible": built["canonical_count"],
        "visible_generated_category_counts": built["visible_counts"],
        "hidden_generated_category_counts": built["hidden_counts"],
        "files": info,
    }
    MANIFEST.write_bytes((json.dumps(manifest, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))
    return info


def check_files() -> None:
    if REGEX_AVAILABLE:
        raise RuntimeError("third-party regex package is active")
    pairs = [
        (VISIBLE_INPUT, VISIBLE_EXPECTED),
        (HIDDEN_INPUT, HIDDEN_EXPECTED),
    ]
    loaded = []
    for source_path, expected_path in pairs:
        sources = decode_lines(source_path.read_bytes())
        expected = decode_lines(expected_path.read_bytes())
        if len(sources) != COUNT or len(expected) != COUNT:
            raise RuntimeError(f"{source_path.name} does not contain {COUNT} records")
        actual = expected_for(sources)
        if actual != expected:
            raise RuntimeError(f"expected output mismatch in {expected_path.name}")
        loaded.append(sources)
    visible, hidden = loaded
    if set(visible) & set(hidden):
        raise RuntimeError("visible and hidden inputs overlap")
    if len(set(visible)) != COUNT or len(set(hidden)) != COUNT:
        raise RuntimeError("duplicate input inside a dataset")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="recompute outputs and compare files")
    args = parser.parse_args()
    if args.check:
        check_files()
        print("check ok")
        return
    built = build()
    info = write_datasets(built)
    check_files()
    print(f"canonical_in_visible={built['canonical_count']}")
    print(f"visible_categories={json.dumps(built['visible_counts'], sort_keys=True)}")
    print(f"hidden_categories={json.dumps(built['hidden_counts'], sort_keys=True)}")
    for name, meta in info.items():
        print(f"{name} bytes={meta['bytes']} sha256={meta['sha256']}")


if __name__ == "__main__":
    main()
