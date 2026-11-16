#!/usr/bin/env python3
"""Generate visible.jsonl and hidden.jsonl test cases for figlet-go Harbor task.

Runs on the host machine using the original pyfiglet library from Step 1.
Freezes exact byte-for-byte outputs by invoking pyfiglet's original main().
Deterministic generation using random.seed(7).
Guarantees 100% unique argument sets within and across visible and hidden sets.
"""

import io
import json
import os
import random
import shutil
import sys
import time
from pathlib import Path

# Locate pyfiglet directory
HERE = Path(__file__).resolve().parent
TASK_DIR = HERE.parent

candidate_dirs = [
    TASK_DIR.parent / "pyfiglet",
    TASK_DIR / "pyfiglet",
    Path.cwd() / "pyfiglet",
    Path.cwd() / "VANAM PRASHANTH" / "pyfiglet",
]

pyfiglet_dir = None
for candidate in candidate_dirs:
    if candidate.is_dir() and (candidate / "pyfiglet" / "__init__.py").exists():
        pyfiglet_dir = candidate.resolve()
        break

if not pyfiglet_dir:
    sys.exit(f"Could not find pyfiglet repository in any candidate location: {candidate_dirs}")

# Ensure pyfiglet/fonts directory is populated from pyfiglet/fonts-standard (Makefile step)
fonts_dir = pyfiglet_dir / "pyfiglet" / "fonts"
fonts_std = pyfiglet_dir / "pyfiglet" / "fonts-standard"
if not fonts_dir.exists():
    shutil.copytree(fonts_std, fonts_dir)
elif len(list(fonts_dir.glob("*.flf"))) == 0:
    for f in fonts_std.glob("*"):
        shutil.copy(f, fonts_dir / f.name)

# Add pyfiglet to import path
sys.path.insert(0, str(pyfiglet_dir))
import pyfiglet

class BinaryStdoutWrapper:
    """Captures binary stdout output from pyfiglet.main() detach() call."""
    def __init__(self, raw: io.BytesIO):
        self.raw = raw

    def detach(self):
        return self.raw

    def write(self, s):
        if isinstance(s, bytes):
            self.raw.write(s)
        else:
            self.raw.write(s.encode("utf-8"))

    def flush(self):
        self.raw.flush()

_saved_stdout = sys.stdout
_saved_argv = sys.argv

def run_original_pyfiglet(args: list[str]) -> str | None:
    """Runs pyfiglet.main() with specified arguments and captures stdout byte-for-byte."""
    global _saved_stdout, _saved_argv
    buf = io.BytesIO()
    sys.stdout = BinaryStdoutWrapper(buf)
    sys.argv = ["pyfiglet"] + args
    try:
        ret = pyfiglet.main()
        if ret != 0:
            return None
        return buf.getvalue().decode("utf-8")
    except (Exception, SystemExit):
        return None
    finally:
        sys.stdout = _saved_stdout
        sys.argv = _saved_argv

FONTS = ["standard", "slant", "small", "big", "mini", "banner", "shadow", "script"]
WIDTHS = [10, 20, 40, 60, 80, 120]
JUSTIFY = ["auto", "left", "center", "right"]
DIRECTIONS = ["auto", "left-to-right", "right-to-left"]

SMUSHING_WORDS = [
    # Rule 1: Equal characters
    "||", "//", "\\\\", "==", "++", "**", "xx", "oo", "##", "@@",
    # Rule 2: Lowline / underscore
    "_|", "/_", "\\_", "_[", "_]", "_{", "_}", "_(", "_)", "_<", "_>", "___",
    # Rule 3: Hierarchy
    "|/", "|\\", "|[", "|{", "|(", "|<", "/[", "\\{", "[]", "{}", "()", "<>",
    # Rule 4: Opposite pairs
    "[]", "][", "{}", "}{", "()", ")(", "[[]]", "{{}}", "(())",
    # Rule 5: Big X
    "/\\", "\\/", "><", "/\\/", "\\/\\", "><><", ">> <<",
    # Rule 6 & complex smushing combinations
    "|_|", "\\o/", "/_\\", "[()]", "{[]}", "([{}])", "(<|>)", "<{[(|)]}>",
    "/path/to/file", "[DONE]", "{TEST}", "<FIGLET>", "(OK)", "|test|",
    "| / \\ _ [ ] { } ( ) < >", "$", "$$", "$hello$", "$100",
]

NORMAL_WORDS = [
    "hello", "world", "Harbor", "Go", "Python", "code", "terminal", "banner",
    "quick", "brown", "fox", "jumps", "lazy", "dog", "computer", "system",
    "alpha", "beta", "gamma", "delta", "rock", "paper", "scissors", "space",
    "12345", "2026", "v1.0.4", "42", "100%", "#1", "top", "bot", "run", "yes",
    "simple", "port", "machine", "letters", "giant", "shout", "matrix",
]

LATIN1_WORDS = [
    "café", "élan", "naïve", "piñata", "déjà vu", "façade", "señor", "brûlée",
    "München", "Zürich", "über", "grün", "año", "niño", "cliché", "voilà",
    "é", "ß", "ñ", "ä", "ö", "ü", "Ä", "Ö", "Ü",
    "à", "è", "ù", "á", "í", "ó", "ú",
]

MISSING_CHAR_WORDS = [
    "price: 10€", "Python™ 3", "hello ★ world", "alpha λ beta", "© 2026",
    "test ® mark", "100¥", "happy ☺ day", "漢字", "sum ∑ all", "temp 25°C",
]

DOUBLE_SPACE_WORDS = [
    "hello  world", "foo   bar", "double  space", "  leading", "trailing  ",
    "a  b  c", "two  spaces  here", "   multi   space   ",
]

LONG_SENTENCES = [
    "The quick brown fox jumps over the lazy dog repeatedly until the line wraps",
    "This is a long sentence designed specifically to test FIGlet text wrapping at narrow column limits",
    "To be or not to be that is the question whether tis nobler in the mind to suffer",
    "A stitch in time saves nine but giant ASCII letters wrap when width is small",
    "Long line of text that exceeds standard terminal width and tests line breaking rules",
    "Lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor incididunt ut labore",
]

SINGLE_CHARS = [
    "|", "/", "\\", "_", "[", "]", "{", "}", "(", ")", "<", ">",
    "A", "Z", "a", "z", "0", "9", "X", "Y", "é", "ß", "ñ",
]

# Preload fonts to check character widths
FONT_OBJS = {f: pyfiglet.FigletFont(f) for f in FONTS}

def generate_random_text() -> str:
    category = random.choice([
        "smush", "normal", "latin1", "missing", "doublespace", "long", "single", "mixed"
    ])
    if category == "smush":
        return random.choice(SMUSHING_WORDS)
    elif category == "normal":
        count = random.randint(1, 3)
        return " ".join(random.sample(NORMAL_WORDS, count))
    elif category == "latin1":
        return random.choice(LATIN1_WORDS)
    elif category == "missing":
        return random.choice(MISSING_CHAR_WORDS)
    elif category == "doublespace":
        return random.choice(DOUBLE_SPACE_WORDS)
    elif category == "long":
        return random.choice(LONG_SENTENCES)
    elif category == "single":
        return random.choice(SINGLE_CHARS)
    else:
        # Mixed: tricky pattern + normal word
        p = random.choice(SMUSHING_WORDS)
        w = random.choice(NORMAL_WORDS)
        return f"{p} {w}" if random.random() < 0.5 else f"{w} {p}"

def generate_cases(n: int, seen_args: set[tuple[str, ...]], max_attempts: int = 100000) -> list[dict]:
    cases = []
    attempts = 0
    while len(cases) < n:
        attempts += 1
        if attempts > max_attempts:
            raise RuntimeError(
                f"Candidate pool is insufficient to generate {n} unique cases "
                f"(stalled after {len(cases)} cases, {attempts} attempts)"
            )

        font = random.choice(FONTS)
        width = random.choice(WIDTHS)
        justify = random.choice(JUSTIFY)
        direction = random.choice(DIRECTIONS)

        # -r, -F, -s, -n each on in 1 of 4 cases
        use_r = (random.random() < 0.25)
        use_F = (random.random() < 0.25)
        use_s = (random.random() < 0.25)
        use_n = (random.random() < 0.25)

        text = generate_random_text()

        args = ["-f", font, "-w", str(width), "-j", justify, "-D", direction]
        if use_r:
            args.append("-r")
        if use_F:
            args.append("-F")
        if use_s:
            args.append("-s")
        if use_n:
            args.append("-n")

        # Pass text argument
        args.append(text)

        # Enforce global uniqueness: reject if this exact argument set was already selected
        key = tuple(args)
        if key in seen_args:
            continue

        # pyfiglet requires width > char_width for every character in text
        font_obj = FONT_OBJS[font]
        if any(font_obj.width.get(ord(c), 0) >= width for c in text):
            continue

        out = run_original_pyfiglet(args)
        if out is None:
            continue

        seen_args.add(key)
        cases.append({"args": args, "out": out})

    return cases

def main():
    print("Setting random seed to 7...", flush=True)
    random.seed(7)

    data_dir = HERE / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    # Shared global set ensuring 100% unique argument combinations across visible and hidden datasets
    seen_args: set[tuple[str, ...]] = set()

    t0 = time.time()
    print("Generating 2000 unique visible cases...", flush=True)
    visible_cases = generate_cases(2000, seen_args)
    visible_path = data_dir / "visible.jsonl"
    with open(visible_path, "w", encoding="utf-8") as f:
        for c in visible_cases:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    print(f"Wrote 2000 unique visible cases to {visible_path} ({time.time() - t0:.2f}s)", flush=True)

    t1 = time.time()
    print("Generating 2000 unique hidden cases (zero overlap with visible)...", flush=True)
    hidden_cases = generate_cases(2000, seen_args)
    hidden_path = data_dir / "hidden.jsonl"
    with open(hidden_path, "w", encoding="utf-8") as f:
        for c in hidden_cases:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    print(f"Wrote 2000 unique hidden cases to {hidden_path} ({time.time() - t1:.2f}s)", flush=True)

    # Final assertion check
    vis_keys = {tuple(c["args"]) for c in visible_cases}
    hid_keys = {tuple(c["args"]) for c in hidden_cases}
    assert len(vis_keys) == 2000, f"Expected 2000 unique visible cases, got {len(vis_keys)}"
    assert len(hid_keys) == 2000, f"Expected 2000 unique hidden cases, got {len(hid_keys)}"
    assert len(vis_keys.intersection(hid_keys)) == 0, f"Found {len(vis_keys.intersection(hid_keys))} overlapping cases"

    print(f"Done! All 4000 cases verified: 100% unique, 0 overlap in {time.time() - t0:.2f}s.", flush=True)

if __name__ == "__main__":
    main()
