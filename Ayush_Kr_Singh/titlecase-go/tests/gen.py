#!/usr/bin/env python3
"""Generate deterministic visible and hidden titlecase test datasets."""

from pathlib import Path
import random
import sys

TESTS_DIR = Path(__file__).resolve().parent
TASK_DIR = TESTS_DIR.parent
DATA_DIR = TESTS_DIR / "data"

# Locate original python-titlecase source
CANDIDATE_REPOS = [
    TASK_DIR.parent.parent / "python-titlecase",
    TASK_DIR.parent / "python-titlecase",
    TASK_DIR / "environment" / "repo",
]
for repo_path in CANDIDATE_REPOS:
    if (repo_path / "titlecase" / "__init__.py").is_file():
        sys.path.insert(0, str(repo_path))
        break
else:
    raise RuntimeError("Could not locate python-titlecase repository")

from titlecase import titlecase  # noqa: E402

NORMAL_WORDS = [
    "lord", "rings", "house", "dragon", "shadow", "mountain", "river",
    "valley", "garden", "bridge", "station", "market", "harbor", "lighthouse",
    "morning", "evening", "winter", "summer", "autumn", "spring", "cloud",
    "storm", "forest", "desert", "island", "ocean", "planet", "rocket",
    "engine", "system", "method", "design", "theory", "practice", "guide",
    "manual", "report", "notes", "story", "chronicle", "journey", "quest",
    "secret", "castle", "tower", "gate", "silver", "golden", "crystal",
    "ancient", "modern", "future", "simple", "complex", "hidden", "broken",
]

SMALL_WORDS = [
    "a", "an", "and", "as", "at", "but", "by", "en", "for", "if",
    "in", "of", "on", "or", "the", "to", "v", "v.", "via", "vs", "vs.",
]

TRICKY_TOKENS = [
    # Dotted initials
    "U.S.", "A.B.C.", "J.R.", "U.K.", "E.U.",
    # Apostrophe second character (straight and curly)
    "d'artagnan", "D'ARTAGNAN", "d'artagnan's", "l'enfant", "L'ÉTAT",
    "o'malley", "O'BRIEN", "o'clock", "d’artagnan", "l’homme", "o’reilly",
    # Mc / MC prefixes (and Mac non-match)
    "mcgovern", "MCINTOSH", "mcDonald", "McBride", "macintosh", "MACARTHUR",
    # Honorifics
    "mr", "mrs", "ms", "dr", "MR", "MRS", "MS", "DR", "mr.", "dr.",
    # Inline period / URL / camelCase / internal caps
    "example.com", "e.g.", "i.e.", "v1.2", "iPhone", "iPad", "eBay",
    "YouTube", "AT&T", "Q&A", "MacBook", "macOS", "GitHub",
    "https://example.com/a-b", "http://foo.org/the-end",
    # Slashed compounds
    "and/or", "word/word", "a/the/end", "this/is/a/test",
    "two-not-three/three-by-four", "dance/let's",
    # Hyphenated compounds
    "end-to-end", "two-not-three", "a-b", "in-the-middle", "state-of-the-art",
    "up-to-date", "step-by-step", "five-and",
    # All-consonant acronyms vs <= 2 chars vs 'y'
    "cnn", "bbc", "mph", "html", "http", "sql", "st", "nd", "rd", "rhythm", "xyz",
    # Ordinals & digits
    "34th", "3rd", "2nd", "1st", "2026",
    # Quoted / punctuated words
    "'hello", "world'", '"the', 'end"', "(a", "test)", "afraid?", "done!",
    "‘quote", "word’", "“quoted”",
]

SUBPHRASE_SEPS = [": ", ". ", "; ", "? ", "! ", "- ", "– ", "— "]
WHITESPACE_SEPS = [" ", " ", " ", " ", "\t", "  "]


def make_title(rng: random.Random, index: int) -> str:
    """Generate a single-line title exercising normal and edge-case rules."""
    # Guaranteed edge cases at early indices
    if index == 0:
        return ""
    if index == 1:
        return "the lord of the rings"
    if index == 2:
        return "v. and vs. and en"
    if index == 3:
        return "d'artagnan and o'malley at mcgovern's"
    if index == 4:
        return "DR JONES AND U.S. POLICY ON CNN"

    mode = rng.random()
    n_words = rng.randint(1, 9)
    tokens = []
    for pos in range(n_words):
        roll = rng.random()
        if roll < 0.35:
            tok = rng.choice(SMALL_WORDS)
        elif roll < 0.70:
            tok = rng.choice(TRICKY_TOKENS)
        else:
            tok = rng.choice(NORMAL_WORDS)

        # Randomly vary casing of single token
        case_roll = rng.random()
        if case_roll < 0.15:
            tok = tok.upper()
        elif case_roll < 0.30:
            tok = tok.lower()
        elif case_roll < 0.40:
            tok = tok.capitalize()

        # Occasionally wrap in punctuation
        if rng.random() < 0.12:
            left = rng.choice(["'", '"', "(", "‘", "“", ""])
            right = rng.choice(["'", '"', ")", ",", ".", "!", "?", "’", "”", ""])
            tok = f"{left}{tok}{right}"

        tokens.append(tok)

    # Join with spaces, tabs, or subphrase punctuation + space
    parts = [tokens[0]]
    for tok in tokens[1:]:
        if rng.random() < 0.18:
            sep = rng.choice(SUBPHRASE_SEPS)
        else:
            sep = rng.choice(WHITESPACE_SEPS)
        parts.append(sep)
        parts.append(tok)

    line = "".join(parts)
    if mode < 0.20:
        line = line.upper()
    elif mode < 0.35:
        line = line.lower()

    # Ensure strictly single-line (no embedded CR/LF)
    return line.replace("\r", "").replace("\n", "")


def generate_unique_dataset(rng: random.Random, count: int, seen: set[str]) -> list[str]:
    """Generate `count` unique single-line titles not present in `seen`."""
    lines: list[str] = []
    idx = 0
    while len(lines) < count:
        candidate = make_title(rng, idx if not seen else idx + 10)
        idx += 1
        if candidate not in seen:
            seen.add(candidate)
            lines.append(candidate)
    return lines


def write_dataset(inputs_path: Path, expected_path: Path, lines: list[str]) -> None:
    expected_lines = []
    for line in lines:
        out = titlecase(line)
        if "\n" in out or "\r" in out:
            raise ValueError(f"Unexpected newline in titlecase output for {line!r}")
        expected_lines.append(out)

    inputs_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    expected_path.write_text("\n".join(expected_lines) + "\n", encoding="utf-8")


def main() -> None:
    random.seed(1)
    rng = random.Random(1)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    seen: set[str] = set()
    visible_inputs = generate_unique_dataset(rng, 2000, seen)
    hidden_inputs = generate_unique_dataset(rng, 2000, seen)

    write_dataset(DATA_DIR / "inputs.txt", DATA_DIR / "expected.txt", visible_inputs)
    write_dataset(
        DATA_DIR / "hidden_inputs.txt",
        DATA_DIR / "hidden_expected.txt",
        hidden_inputs,
    )
    print(f"Wrote {len(visible_inputs)} visible and {len(hidden_inputs)} hidden pairs.")


if __name__ == "__main__":
    main()

