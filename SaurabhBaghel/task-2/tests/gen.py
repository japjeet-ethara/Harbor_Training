#!/usr/bin/env python3
"""
Test generator for figlet Harbor task.
Generates 2000 visible cases and 2000 hidden test cases using pyfiglet.
Deterministic with random.seed(7).
"""

import io
import json
import os
import random
import sys

# Locate and import pyfiglet
possible_paths = [
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "pyfiglet")),
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "pyfiglet")),
    os.path.abspath(os.path.join(os.getcwd(), "pyfiglet")),
]
for p in possible_paths:
    if os.path.isdir(p):
        sys.path.insert(0, p)
        break

try:
    import pyfiglet
except ImportError:
    print("Error: Could not import pyfiglet. Please ensure pyfiglet repository is present.")
    sys.exit(1)

FONTS = ["standard", "slant", "small", "big", "mini", "banner", "shadow", "script"]
WIDTHS = [10, 20, 40, 60, 80, 120]
JUSTIFICATIONS = ["auto", "left", "center", "right"]
DIRECTIONS = ["auto", "left-to-right", "right-to-left"]

WORDS = [
    "hello", "world", "figlet", "harbor", "agent", "twin", "machine", "letters",
    "shout", "giant", "test", "docker", "python", "golang", "code", "terminal",
    "kernel", "buffer", "matrix", "vector", "stream", "parser", "layout", "font"
]

RARE_CASES = [
    "|_|", "/\\", "\\/", "<>", "><", "{}", "[]", "()", "_/_", "\\_/",
    "| / \\ _ [ ] { } ( ) < >", "///\\\\\\", "[_]", "(/)", "<|>",
    "foo_bar", "[test]", "(hello)", "<world>", "{data}", "x = a | b;",
    "|||", "___", "///", "\\\\\\", "<<<", ">>>", "{{{", "}}}", "[[[", "]]]"
]

DOUBLE_SPACES = [
    "hello  world", "  spaced  out  ", "a  b  c  d", "smush  ||  test", "left   right"
]

LONG_SENTENCES = [
    "The quick brown fox jumps over the lazy dog repeatedly until it wraps.",
    "When two giant letters stand next to each other the program squeezes them together.",
    "FIGlet is a program that creates large characters out of ordinary screen characters.",
    "Every smushing rule must be copied exactly space for space across all widths and options."
]

LATIN1 = [
    "café", "Über", "naïve", "façade", "München", "Señor", "Straße", "Äpfel",
    "é ß ñ", "ä ö ü Ä Ö Ü ß", "crème brûlée", "piñata"
]

MISSING_CHARS = [
    "hello @#%^&* world", "test € ¢ ¥", "math ∑ ∫ √", "status 😀 🚀 ok", "sym § ¶ © ® ™"
]

ALL_TEXT_POOLS = [
    WORDS, RARE_CASES, DOUBLE_SPACES, LONG_SENTENCES, LATIN1, MISSING_CHARS
]

# Preload and cache fonts
font_objs = {f: pyfiglet.Figlet(font=f).Font for f in FONTS}

font_cache = {}
_orig_init = pyfiglet.FigletFont.__init__

def _cached_font_init(self, font=pyfiglet.DEFAULT_FONT):
    if font in font_cache:
        cached = font_cache[font]
        self.font = cached.font
        self.comment = cached.comment
        self.chars = cached.chars
        self.width = cached.width
        self.data = cached.data
        self.height = cached.height
        self.hardBlank = cached.hardBlank
        self.printDirection = cached.printDirection
        self.smushMode = cached.smushMode
    else:
        _orig_init(self, font)
        font_cache[font] = self

pyfiglet.FigletFont.__init__ = _cached_font_init


class DummyStdout(io.TextIOWrapper):
    def __init__(self):
        self.buf = io.BytesIO()
        super().__init__(self.buf, encoding="utf-8")

    def detach(self):
        return self.buf


def run_pyfiglet(args):
    old_argv = sys.argv
    old_stdout = sys.stdout
    fake = DummyStdout()
    sys.argv = ["pyfiglet"] + args
    sys.stdout = fake
    try:
        ret = pyfiglet.main()
        if ret != 0 and ret is not None:
            return None
        return fake.buf.getvalue().decode("utf-8")
    except Exception:
        return None
    finally:
        sys.argv = old_argv
        sys.stdout = old_stdout


def is_valid_for_font_width(font_name, width, text):
    f_obj = font_objs[font_name]
    for ch in text:
        w = f_obj.width.get(ord(ch), 0)
        # pyfiglet hangs in an infinite loop or raises CharNotPrinted if w >= width
        if w >= width:
            return False
    return True


def generate_candidate_args(rng):
    font = rng.choice(FONTS)
    width = rng.choice(WIDTHS)
    justify = rng.choice(JUSTIFICATIONS)
    direction = rng.choice(DIRECTIONS)

    # Pick text from pools
    pool = rng.choice(ALL_TEXT_POOLS)
    text = rng.choice(pool)

    # Occasionally combine two words/tokens
    if rng.random() < 0.3:
        pool2 = rng.choice(ALL_TEXT_POOLS)
        text = text + " " + rng.choice(pool2)

    if not is_valid_for_font_width(font, width, text):
        return None

    args = ["-f", font, "-w", str(width), "-j", justify, "-D", direction]

    # Flags each on in 1 of 4 cases (p = 0.25)
    if rng.random() < 0.25:
        args.append("-r")
    if rng.random() < 0.25:
        args.append("-F")

    s_flag = rng.random() < 0.25
    n_flag = rng.random() < 0.25
    if s_flag:
        args.append("-s")
    if n_flag:
        args.append("-n")

    args.append(text)
    return args


def generate_dataset(count, rng, seen_set):
    cases = []
    while len(cases) < count:
        args = generate_candidate_args(rng)
        if args is None:
            continue

        key = tuple(args)
        if key in seen_set:
            continue

        out = run_pyfiglet(args)
        if out is None:
            continue

        seen_set.add(key)
        cases.append({"args": args, "out": out})

    return cases


def main():
    rng = random.Random(7)
    seen_set = set()

    data_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(data_dir, exist_ok=True)

    print("Generating 2000 visible cases...")
    visible_cases = generate_dataset(2000, rng, seen_set)
    visible_path = os.path.join(data_dir, "visible.jsonl")
    with open(visible_path, "w", encoding="utf-8", newline="\n") as f:
        for c in visible_cases:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    print(f"Wrote {len(visible_cases)} visible cases to {visible_path}")

    print("Generating 2000 hidden cases (disjoint from visible)...")
    hidden_cases = generate_dataset(2000, rng, seen_set)
    hidden_path = os.path.join(data_dir, "hidden.jsonl")
    with open(hidden_path, "w", encoding="utf-8", newline="\n") as f:
        for c in hidden_cases:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    print(f"Wrote {len(hidden_cases)} hidden cases to {hidden_path}")

    # Check intersection
    visible_keys = {tuple(c["args"]) for c in visible_cases}
    hidden_keys = {tuple(c["args"]) for c in hidden_cases}
    overlap = visible_keys.intersection(hidden_keys)
    print(f"Overlap between visible and hidden: {len(overlap)}")
    assert len(overlap) == 0, "Visible and hidden datasets must be completely disjoint!"
    print("Datasets successfully verified!")


if __name__ == "__main__":
    main()
