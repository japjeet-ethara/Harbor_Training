"""Freeze deterministic titlecase inputs and Python answers.

Expected files are produced by running the original titlecase() function.
Do not edit them by hand.
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

def task_root() -> Path:
    """Task root, from this file's location. The working directory is irrelevant."""
    here = Path(__file__).resolve()
    for parent in (here.parent, *here.parents):
        py_init = parent / "environment" / "python-titlecase" / "titlecase" / "__init__.py"
        if py_init.is_file() and (parent / "tests").is_dir():
            return parent
    raise SystemExit(f"could not find the task root from {here}")


ROOT = task_root()
PY_REPO = ROOT / "environment" / "python-titlecase"
sys.path.insert(0, str(PY_REPO))

from titlecase import titlecase  # noqa: E402
from titlecase.tests import TEST_DATA  # noqa: E402

DATA = ROOT / "tests" / "data"
N = 2000

WORDS = [
    "lord", "rings", "apple", "jobs", "washington", "episode", "force",
    "music", "dance", "string", "title", "plane", "snakes", "technology",
    "problem", "nothing", "afraid", "example", "lines", "franco",
    "permissions", "voodoo", "spool", "gruber", "omnifocus", "consonants",
    "cnn", "html", "css", "nasa", "sec", "probe", "know", "trick",
    "perhaps", "quotes", "hyphen", "machine", "st", "foo", "bar", "end",
    "iphone", "itunes", "thoughts", "repair", "reading", "steve", "music",
    "harbor", "docker", "python", "titlecase", "acronym", "small", "word",
    "php", "rhythm", "sky", "myth", "ftp", "http", "www", "com", "org",
    "mcdonald", "oblon", "spivak", "maier", "neustadt", "clelland",
    "generalissimo", "francisco", "jackass", "kieren", "mccarthy",
    "vapo", "rware", "omnifocus", "gruber", "listed", "something",
    "between", "still", "dead", "famous", "edit", "awakens", "young",
    "restless", "afraid", "start", "within", "quotes", "sub", "phrase",
]

SMALL = [
    "a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in",
    "of", "on", "or", "the", "to", "v", "v.", "via", "vs", "vs.",
]

SEPARATORS = [" ", "  ", "\t", " - ", ": ", "; ", " - ", ". ", "? "]


def rand_case(rng: random.Random, word: str) -> str:
    kind = rng.randrange(5)
    if kind == 0:
        return word.lower()
    if kind == 1:
        return word.upper()
    if kind == 2:
        return word.capitalize()
    chars = []
    for ch in word:
        chars.append(ch.upper() if rng.random() < 0.4 else ch.lower())
    return "".join(chars)


def word(rng: random.Random) -> str:
    return rand_case(rng, rng.choice(WORDS))


def token(rng: random.Random) -> str:
    kind = rng.randrange(14)
    if kind == 0:
        return rng.choice(SMALL)
    if kind == 1:
        return rand_case(rng, rng.choice(SMALL))
    if kind == 2:
        return rng.choice(["Mc", "mc", "MC", "Mac", "mac"]) + word(rng)
    if kind == 3:
        return rng.choice(["o'", "O'", "d'", "D'", "l'", "L'"]) + word(rng)
    if kind == 4:
        parts = [word(rng) if rng.random() < 0.7 else rng.choice(SMALL) for _ in range(rng.randint(2, 4))]
        return "-".join(parts)
    if kind == 5:
        parts = [word(rng) if rng.random() < 0.6 else rng.choice(SMALL) for _ in range(rng.randint(2, 3))]
        return "/".join(parts)
    if kind == 6:
        host = rng.choice(["example.com", "foo.com", "del.icio.us", "news.ycombinator.com"])
        return rng.choice(["http://", "https://", "www."]) + host + "/" + word(rng).lower()
    if kind == 7:
        letters = [chr(rng.randrange(65, 91)) for _ in range(rng.randint(2, 4))]
        return ".".join(letters) + "."
    if kind == 8:
        punct = rng.choice(list(".,;:?!\"'"))
        base = word(rng)
        return punct + base if rng.random() < 0.5 else base + punct
    if kind == 9:
        q = rng.choice(["'", '"'])
        return q + word(rng) + q
    if kind == 10:
        return rand_case(rng, rng.choice(["cnn", "html", "css", "php", "ftp", "nasa", "tv", "sec", "att", "q&a"]))
    if kind == 11:
        return word(rng)
    if kind == 12:
        return rng.choice(["Mr", "mr", "Mrs", "Ms", "Mss", "Dr", "dr", "MR", "DR"]) + rng.choice(["", "."])
    return word(rng)


def make_line(rng: random.Random) -> str:
    roll = rng.random()
    if roll < 0.04:
        return rng.choice([" ", "  ", "\t"])
    n = rng.randint(1, 8)
    parts = [token(rng) for _ in range(n)]
    sep = rng.choice(SEPARATORS)
    line = sep.join(parts)
    if rng.random() < 0.12:
        line = line.upper()
    if rng.random() < 0.08:
        line = rng.choice(["(", '"', "'"]) + line
    line = line.replace("\r", " ").replace("\n", " ")
    if not line.isascii():
        raise SystemExit(f"generator emitted a non-ASCII line: {line!r}")
    return line


def official_lines() -> list[str]:
    lines = []
    seen = set()
    for src, _expected in TEST_DATA:
        pieces = src.splitlines()
        # A multiline titlecase() call is not the line-oriented contract.
        # Empty pieces are omitted: one input line never contains a newline.
        if len(pieces) != 1 or "\n" in src or "\r" in src:
            pieces = [p for p in src.splitlines() if p != ""]
        for piece in pieces:
            if piece == "" or piece in seen or not piece.isascii():
                continue
            if titlecase(piece) == piece:
                continue
            seen.add(piece)
            lines.append(piece)
    return lines


def answer(line: str) -> str:
    got = titlecase(line)
    if "\n" in got or "\r" in got:
        raise SystemExit(f"titlecase introduced a newline for {line!r} -> {got!r}")
    if not got.isascii():
        raise SystemExit(f"titlecase returned non-ASCII for {line!r} -> {got!r}")
    return got


def write_pair(inputs: list[str], in_name: str, out_name: str) -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    in_path = DATA / in_name
    out_path = DATA / out_name
    with in_path.open("w", encoding="utf-8", newline="\n") as inf, out_path.open(
        "w", encoding="utf-8", newline="\n"
    ) as outf:
        for line in inputs:
            got = answer(line)
            if got == line:
                raise SystemExit(f"titlecase left a line unchanged: {line!r}")
            inf.write(line + "\n")
            outf.write(got + "\n")
    in_n = in_path.read_text(encoding="utf-8").count("\n")
    out_n = out_path.read_text(encoding="utf-8").count("\n")
    if in_n != out_n or in_n != len(inputs):
        raise SystemExit(f"line count mismatch for {in_name}: {in_n} vs {out_n}")


def take_unique(rng: random.Random, n: int, banned: set[str]) -> list[str]:
    """Draw n lines that are unique, absent from banned, and changed by titlecase()."""
    lines: list[str] = []
    seen = set(banned)
    attempts = 0
    limit = n * 200
    while len(lines) < n:
        attempts += 1
        if attempts > limit:
            raise SystemExit(f"could not draw {n} unique lines ({len(lines)} so far)")
        line = make_line(rng)
        if line in seen or answer(line) == line:
            continue
        seen.add(line)
        lines.append(line)
    return lines


def main() -> None:
    rng = random.Random(1)
    official = official_lines()
    if len(official) > N:
        raise SystemExit("too many official lines")
    # Hidden keeps the library's own examples. Visible must not reuse them,
    # and the random hidden lines must not reuse visible or official lines.
    visible = take_unique(rng, N, set(official))
    hidden = take_unique(rng, N - len(official), set(visible) | set(official)) + official
    write_pair(visible, "inputs.txt", "expected.txt")
    write_pair(hidden, "hidden_inputs.txt", "hidden_expected.txt")
    overlap = set(visible) & set(hidden)
    if overlap:
        raise SystemExit(f"visible/hidden overlap: {len(overlap)}")
    print(f"wrote {N} visible and {N} hidden lines ({len(official)} official in hidden)")


if __name__ == "__main__":
    main()
