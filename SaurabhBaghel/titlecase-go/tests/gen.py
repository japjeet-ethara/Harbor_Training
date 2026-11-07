"""Generate deterministic titlecase fixtures from the original Python library.

Run from the repository root:

    uv run --with regex==2024.11.6 python tests/gen.py

The optional ``regex`` package is required so ``titlecase()`` takes the same
branch as the task environment. Expected files are never written by hand.
"""

from __future__ import annotations

import hashlib
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT / "environment" / "repo"
DATA = Path(__file__).resolve().parent / "data"
COUNT = 2000

SMALL = [
    "a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in",
    "of", "on", "or", "the", "to", "v", "v.", "via", "vs", "vs.",
]
WORDS = [
    "lord", "rings", "apple", "nasa", "html", "cnn", "itunes", "iphone",
    "mcfoo", "macdonalds", "state", "art", "end", "known", "york", "queen",
    "café", "über", "naïve", "élite", "niño", "phd", "q&a", "at&t", "5th",
    "3rd", "st", "ok", "why", "rhythm", "co", "op", "email", "example",
    "spider", "force", "awakens", "quote", "young", "restless", "plane",
    "music", "dance", "technology", "permissions", "voodoo", "jackass",
    "washington", "problem", "deal", "probe", "string", "title", "world",
    "москва", "ελλάδα", "中文", "עברית", "øst", "æther",
]
LEAD = list("\"'“‘([{")
TAIL = ["", ".", "?", "!", "'", "\"", "?", ".'"]
SPACES = [" ", "  ", "\t", "\u00a0", "\u2002", "\u2003", "\u2009", "\u200a", "\u202f", "\u3000"]
BREAKS = [": ", "; ", " - ", " — ", " – ", "? ", "! ", ", "]


def _sentence(rng: random.Random, n: int) -> str:
    return rng.choice(SPACES).join(rng.choice(WORDS + SMALL) for _ in range(n))


def _one(rng: random.Random) -> str:
    kind = rng.randrange(18)
    if kind == 0:
        return _sentence(rng, rng.randint(1, 8))
    if kind == 1:
        return _sentence(rng, rng.randint(2, 7)).upper()
    if kind == 2:
        return "-".join(rng.choice(WORDS + SMALL) for _ in range(rng.randint(2, 4)))
    if kind == 3:
        parts = [rng.choice(WORDS + SMALL) for _ in range(rng.randint(2, 4))]
        return "/".join(parts)
    if kind == 4:
        return rng.choice(LEAD) + _sentence(rng, rng.randint(2, 6)) + rng.choice(TAIL)
    if kind == 5:
        return _sentence(rng, rng.randint(1, 4)) + rng.choice(BREAKS) + _sentence(rng, rng.randint(1, 4))
    if kind == 6:
        return rng.choice(["Mc", "mc", "MC", "Mac"]) + rng.choice(
            ["Donalds", "Tavish", "Foo-bar", "bar", "Ab", "HTML", "Cay-mcbut"]
        )
    if kind == 7:
        return (
            rng.choice(["o", "O", "l", "L", "d", "D"])
            + rng.choice(["'", "‘"])
            + rng.choice(["reilly", "grange", "REILLY", "Grange", "oyle's", "artagnan"])
        )
    if kind == 8:
        base = _sentence(rng, rng.randint(2, 5))
        return "".join(ch.upper() if rng.random() < 0.3 else ch for ch in base)
    if kind == 9:
        return rng.choice(["http://", "https://", ""]) + rng.choice(
            ["foo.com", "example.com", "a.b", "del.icio.us"]
        ) + rng.choice(["", "/bar", "/a/b"])
    if kind == 10:
        return rng.choice(SPACES).join(_sentence(rng, 1) for _ in range(3))
    if kind == 11:
        return "X ≤ " + str(rng.randint(0, 20))
    if kind == 12:
        return rng.choice(["", "the ", "a "]) + rng.choice(WORDS) + rng.choice(["'s", "’s", ""])
    if kind == 13:
        alphabet = [0x41, 0x61, 0xC9, 0xE9, 0xD1, 0xF1, 0x4E2D, 0x391, 0x3B1, 0x5D0, 0xC6, 0xE6]
        return "".join(chr(rng.choice(alphabet)) for _ in range(rng.randint(1, 12)))
    if kind == 14:
        return rng.choice(["D.C.", "U.S.", "U.S.A.", "F.B.I.", "A.B.", "Ph.D.", "e.g.", "i.e.", "iTunes", "iPhone", "MacDonalds"])
    if kind == 15:
        return _sentence(rng, rng.randint(1, 3)) + " and/or " + _sentence(rng, rng.randint(1, 3))
    if kind == 16:
        return rng.choice(["Mr", "mr", "Mrs", "Ms", "Dr", "dr", "Mss"]) + " " + _sentence(rng, rng.randint(1, 4))
    return _sentence(rng, rng.randint(3, 6)) + rng.choice(BREAKS) + _sentence(rng, rng.randint(1, 3))


def _official() -> list[str]:
    sys.path.insert(0, str(REPO))
    from titlecase.tests import TEST_DATA

    lines = []
    for src, _expected in TEST_DATA:
        if "\n" in src or "\r" in src or "\x00" in src:
            continue
        lines.append(src)
    return lines


def _generate(rng: random.Random, official: list[str]) -> list[str]:
    lines = [_one(rng) for _ in range(COUNT)]
    # Place each official case in its own slot. Visible and hidden draws use
    # later positions in the same seeded stream, so the slots differ.
    for slot, case in zip(rng.sample(range(COUNT), len(official)), official):
        lines[slot] = case
    for line in lines:
        if "\n" in line or "\r" in line:
            raise SystemExit("generator produced a line break")
    return lines


def _write(name: str, lines: list[str]) -> None:
    path = DATA / name
    path.write_bytes(("\n".join(lines) + "\n").encode("utf-8"))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    sys.path.insert(0, str(REPO))
    from titlecase import titlecase

    if not getattr(sys.modules["titlecase"], "REGEX_AVAILABLE", False):
        raise SystemExit("regex package is not installed; refuse to freeze answers")

    rng = random.Random(1)
    official = _official()
    visible = _generate(rng, official)
    hidden = _generate(rng, official)
    visible_expected = [titlecase(line) for line in visible]
    hidden_expected = [titlecase(line) for line in hidden]
    overlap = sum(a == b for a, b in zip(visible_expected, hidden_expected))
    if overlap / COUNT >= 0.01:
        raise SystemExit(f"visible/hidden overlap too high: {overlap}/{COUNT}")

    DATA.mkdir(parents=True, exist_ok=True)
    _write("inputs.txt", visible)
    _write("expected.txt", visible_expected)
    _write("hidden_inputs.txt", hidden)
    _write("hidden_expected.txt", hidden_expected)
    for name in ("inputs.txt", "expected.txt", "hidden_inputs.txt", "hidden_expected.txt"):
        text = (DATA / name).read_text(encoding="utf-8")
        count = text.splitlines()
        if len(count) != COUNT:
            raise SystemExit(f"{name} has {len(count)} lines")
        print(f"{name} {len(count)} {_sha(DATA / name)}")
    print(f"positional_expected_overlap {overlap}")


if __name__ == "__main__":
    main()
