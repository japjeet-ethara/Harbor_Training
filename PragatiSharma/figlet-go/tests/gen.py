#!/usr/bin/env python3
"""
Test generator for figlet-go Harbor assignment.
Generates 2,000 cases in figlet-go/tests/data/visible.jsonl and
2,000 cases in figlet-go/tests/data/hidden.jsonl by running pyfiglet
and capturing stdout byte-for-byte.
"""

import json
import os
import pathlib
import random
import subprocess
import sys
import time

# Set random seed as required
random.seed(7)

# Resolve paths relative to script location
SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
TESTS_DIR = SCRIPT_DIR
FIGLET_GO_DIR = TESTS_DIR.parent
WORKSPACE_DIR = FIGLET_GO_DIR.parent
PYFIGLET_DIR = (WORKSPACE_DIR / "pyfiglet").resolve()

# Add local pinned pyfiglet checkout to sys.path to import FigletFont
if str(PYFIGLET_DIR) not in sys.path:
    sys.path.insert(0, str(PYFIGLET_DIR))

from pyfiglet import FigletFont

DATA_DIR = TESTS_DIR / "data"
VISIBLE_FILE = DATA_DIR / "visible.jsonl"
HIDDEN_FILE = DATA_DIR / "hidden.jsonl"

TARGET_COUNT_PER_FILE = 2000
TIMEOUT_PER_CASE = 15.0  # per-case timeout in seconds

# Cache for loaded FigletFont instances
FONT_CACHE: dict[str, FigletFont] = {}


def get_font(font_name: str) -> FigletFont:
    """Retrieve or load and cache FigletFont instance from local pinned checkout."""
    if font_name not in FONT_CACHE:
        FONT_CACHE[font_name] = FigletFont(font_name)
    return FONT_CACHE[font_name]


def parse_candidate_args(args: list[str]) -> tuple[str, int, list[str]]:
    """Extract font name, width, and positional text arguments from candidate args."""
    font_name = args[args.index("-f") + 1]
    width = int(args[args.index("-w") + 1])
    i = 0
    while i < len(args):
        if args[i] in ("-f", "-w", "-j", "-D"):
            i += 2
        elif args[i] in ("-r", "-F", "-s", "-n"):
            i += 1
        else:
            break
    text_args = args[i:]
    return font_name, width, text_args


def should_skip_glyph_width(font_name: str, width: int, text_args: list[str]) -> bool:
    """
    Check if any non-space character in positional text arguments has a glyph width
    exactly equal to width.
    Uses FigletFont(font_name).width.get(ord(character)) for the lookup.
    """
    font = get_font(font_name)
    for arg in text_args:
        for char in arg:
            if char == " ":
                continue
            char_width = font.width.get(ord(char))
            if char_width == width:
                return True
    return False

# Required fonts and widths
FONTS = [
    "standard",
    "slant",
    "small",
    "big",
    "mini",
    "banner",
    "shadow",
    "script",
]

WIDTHS = [10, 20, 40, 60, 80, 120]

# All justification and direction options
JUSTIFICATIONS = ["auto", "left", "center", "right"]
DIRECTIONS = ["auto", "left-to-right", "right-to-left"]

ORDINARY_WORDS = [
    "hello", "world", "figlet", "harbor", "golang", "python", "terminal",
    "banner", "render", "smush", "kerning", "font", "ascii", "glyph",
    "quick", "brown", "fox", "jumps", "lazy", "dog", "code", "test",
    "suite", "system", "output", "format", "column", "width", "align",
    "reverse", "flip", "strip", "space", "buffer", "matrix", "layout",
    "simple", "sample", "example", "command", "process", "program",
    "library", "string", "character", "stream", "standard", "shadow",
    "slant", "script", "mini", "small", "big", "value", "result",
]

LONG_SENTENCES = [
    "The quick brown fox jumps over the lazy dog repeatedly.",
    "FIGlet is a computer program that generates text banners from ordinary text.",
    "Porting pyfiglet rendering behavior to Go for the Harbor evaluation assignment.",
    "Testing text wrapping behavior across multiple column widths and alignment settings.",
    "Universal overlapping smushing kerning and row reversing with upside down flipping.",
    "Standard output must match the original Python program byte for byte.",
    "Characters wider than the selected terminal width will cause the program to stop.",
    "Normalizing surrounding newlines and stripping leading trailing blank lines.",
    "Smushing rules define how characters share columns when rendered side by side.",
    "Command line interface options are parsed and passed to the FIGlet engine.",
    "Evaluating test cases against reference outputs byte by byte with spaces preserved.",
    "The mirror image reverses each row while flipping turns the picture upside down.",
]

SMUSH_COMBINATIONS = [
    "/\\", "\\/", "/\\/\\", "\\//\\", "/\\/\\/\\", "\\//\\//\\",
    "//\\\\//\\\\", "a/\\b\\/c",
    "[]", "][", "[[[]]]", "][][", "[a][b]", "[|]", "[_]", "[/\\\\]",
    "{}", "}{", "{{{}}}", "}{}{", "{a}{b}", "{|}", "{_}", "{\\/}",
    "()", ")(", "((()))", ")()(", "(a)(b)", "(|)", "(_)", "(/\\)",
    "<>", "><", "<<<>>>", "><><", "<a><b>", "<|>", "<_>", "</\\>",
    "|", "||", "|||", "||||", "|_|", "|/|", "|\\|", "|[|]|", "|{|}|",
    "_{[(<|>)]}_", "[<({|})>]", "><><><", "/>/<\\\\", "{\\_/}", "(>.<)",
    "[_/\\_]", "|/\\[]{}()<>_", "<{([/\\|])}>", "___|___", "_/_\\_"
]

UNDERSCORE_PATTERNS = [
    "_", "__", "___", "____", "_____",
    "__init__", "snake_case_name", "foo_bar_baz", "_test_",
    "_|_", "_/_", "_\\_", "_[_]", "_{_}", "_(_)", "_<_>",
    "__/__", "__\\__", "__||__", "___|___", "_/_\\_"
]

REPEATED_SPACE_TEMPLATES = [
    "hello   world",
    "foo    bar",
    "a  b   c    d",
    "   leading space",
    "trailing space   ",
    "  spaced   out  words  ",
    "   indentation   test",
    "end of line spaces    ",
    "wide     gap     test",
    "|  |   |    |",
    "[  ]   {  }   (  )",
    "F  I  G  L  E  T",
    "H   A   R   B   O   R",
    "   multiple    spaces    everywhere   ",
]

NON_ASCII_TEXTS = [
    "é", "ß", "ñ",
    "éßñ", "é ß ñ",
    "café", "café café", "café latte",
    "Straße", "Groß", "Fußball", "große Straße", "weiß",
    "año", "niño", "señor", "feliz año", "piñata",
    "café Straße año",
    "crème brûlée",
    "Groß résumé niño",
    "café/Straße/año",
    "[café]", "{Straße}", "(año)", "<éßñ>", "|é|ß|ñ|", "é_ß_ñ",
    "café   Straße   año",
    "test café and Straße and año",
]

MISSING_GLYPH_TEXTS = [
    "©", "®", "™", "★", "☺", "♥", "✓", "✗", "•", "§", "¶", "€", "£", "¥", "¿", "¡",
    "中文", "日本語",
    "FIGlet © 2026",
    "Star ★ Rating",
    "Heart ♥ Beat",
    "Check ✓ Done",
    "Cross ✗ Mark",
    "Bullet • Item",
    "Price €100 £50 ¥1000",
    "¿Por qué?",
    "¡Hola Mundo!",
    "Smile ☺ Today",
    "Unicode 中文 test",
    "Section § 42",
    "missing ©®™ glyph",
    "★_★_★",
    "[©] {★} (✓)",
    "café © 2026",
    "Straße § 12",
    "año ★ 2026",
]


def generate_random_text(narrow: bool = False) -> list[str]:
    """Generate text tokens (one or more arguments) covering required patterns."""
    if narrow:
        category = random.choices(
            [
                "short_ordinary",
                "short_smush",
                "short_underscores",
                "short_spaces",
                "short_non_ascii",
                "short_missing",
            ],
            weights=[30, 20, 15, 15, 10, 10],
            k=1,
        )[0]
        if category == "short_ordinary":
            w = random.choice(ORDINARY_WORDS[:25])
            if random.random() < 0.5:
                w = w.capitalize()
            return [w]
        elif category == "short_smush":
            return [random.choice(["/\\", "\\/", "[]", "{}", "()", "<>", "><", "|", "[|]", "{|}", "(_)", "<_>"])]
        elif category == "short_underscores":
            return [random.choice(["_", "__", "_|_", "_/_", "_\\_"])]
        elif category == "short_spaces":
            return [random.choice(["a  b", "x   y", "  hi", "go  "])]
        elif category == "short_non_ascii":
            return [random.choice(["é", "ß", "ñ", "café", "año", "Groß"])]
        else:
            return [random.choice(["©", "★", "✓", "€", "•", "§"])]

    # General text generation covering all required patterns
    category = random.choices(
        [
            "ordinary",
            "repeated_spaces",
            "long_wrapping",
            "slashes",
            "underscores",
            "brackets_braces_parens_angles",
            "vertical_bars_smush",
            "non_ascii",
            "missing_chars",
        ],
        weights=[18, 11, 15, 11, 8, 12, 10, 8, 7],
        k=1,
    )[0]

    if category == "ordinary":
        num_words = random.randint(1, 4)
        words = [random.choice(ORDINARY_WORDS) for _ in range(num_words)]
        if random.random() < 0.3:
            words = [w.capitalize() for w in words]
        elif random.random() < 0.15:
            words = [w.upper() for w in words]
        if len(words) > 1 and random.random() < 0.4:
            return words
        return [" ".join(words)]

    elif category == "repeated_spaces":
        if random.random() < 0.5:
            return [random.choice(REPEATED_SPACE_TEMPLATES)]
        w1 = random.choice(ORDINARY_WORDS)
        w2 = random.choice(ORDINARY_WORDS)
        sp = " " * random.randint(2, 6)
        txt = f"{w1}{sp}{w2}"
        if random.random() < 0.3:
            txt = " " * random.randint(1, 4) + txt
        if random.random() < 0.3:
            txt = txt + " " * random.randint(1, 4)
        return [txt]

    elif category == "long_wrapping":
        if random.random() < 0.6:
            return [random.choice(LONG_SENTENCES)]
        num_words = random.randint(6, 12)
        words = [random.choice(ORDINARY_WORDS) for _ in range(num_words)]
        return [" ".join(words)]

    elif category == "slashes":
        choice = random.choice([
            "/", "//", "///", "\\", "\\\\", "\\\\\\",
            "/\\", "\\/", "/\\/\\", "\\//\\", "/\\/\\/\\",
            "//\\\\//\\\\", "foo/bar", "foo\\bar", "a/b/c", "a\\b\\c"
        ])
        return [choice]

    elif category == "underscores":
        choice = random.choice(UNDERSCORE_PATTERNS)
        return [choice]

    elif category == "brackets_braces_parens_angles":
        choice = random.choice([
            "[]", "][", "[[[]]]", "[a][b]", "[test]",
            "{}", "}{", "{{{}}}", "{a}{b}", "{test}",
            "()", ")(", "((()))", "(a)(b)", "(test)",
            "<>", "><", "<<<>>>", "><><", "<a><b>", "<test>",
            "_{[(<|>)]}_", "[<({|})>]", "><><><", "/>/<\\",
        ])
        if random.random() < 0.3:
            return [choice, random.choice(ORDINARY_WORDS)]
        return [choice]

    elif category == "vertical_bars_smush":
        choice = random.choice(SMUSH_COMBINATIONS)
        return [choice]

    elif category == "non_ascii":
        choice = random.choice(NON_ASCII_TEXTS)
        if random.random() < 0.3:
            return [choice, random.choice(ORDINARY_WORDS)]
        return [choice]

    elif category == "missing_chars":
        choice = random.choice(MISSING_GLYPH_TEXTS)
        if random.random() < 0.3:
            return [choice, random.choice(ORDINARY_WORDS)]
        return [choice]

    return ["hello world"]


def generate_candidate(force_narrow_rtl: bool = False) -> list[str]:
    """Generate a single argument list candidate."""
    if force_narrow_rtl:
        width = random.choice([10, 20])
        direction = "right-to-left"
        font = random.choice(FONTS)
        justify = random.choice(JUSTIFICATIONS)
        text_args = generate_random_text(narrow=(width == 10))
    else:
        font = random.choice(FONTS)
        width = random.choice(WIDTHS)
        justify = random.choice(JUSTIFICATIONS)
        direction = random.choice(DIRECTIONS)
        text_args = generate_random_text(narrow=(width == 10))

    args = [
        "-f", font,
        "-w", str(width),
        "-j", justify,
        "-D", direction,
    ]

    # Choose -r, -F, -s, and -n independently, each with a 1-in-4 chance
    if random.random() < 0.25:
        args.append("-r")
    if random.random() < 0.25:
        args.append("-F")
    if random.random() < 0.25:
        args.append("-s")
    if random.random() < 0.25:
        args.append("-n")

    args.extend(text_args)
    return args


def run_pyfiglet(args: list[str], pyfiglet_dir: pathlib.Path, timeout_sec: float) -> tuple[bool, str]:
    """
    Run [sys.executable, "-m", "pyfiglet", *args] in the original pyfiglet checkout.
    Captures stdout as bytes and decodes as UTF-8, preserving every space and newline.
    If CharNotPrinted is raised for a too-wide glyph, returns (False, "").
    For a timeout, unexpected exit code, subprocess error, or UTF-8 decoding error,
    stops the generator with a nonzero exit and shows the exact args and error.
    """
    env = os.environ.copy()
    env["PYTHONPATH"] = str(pyfiglet_dir)
    env["PYTHONIOENCODING"] = "utf-8"

    cmd = [sys.executable, "-m", "pyfiglet", *args]

    try:
        proc = subprocess.run(
            cmd,
            cwd=str(pyfiglet_dir),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout_sec,
        )
    except subprocess.TimeoutExpired as exc:
        print(f"Error: Subprocess timed out after {timeout_sec}s for args: {args}\n{exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"Error: Subprocess execution error for args: {args}\n{exc}", file=sys.stderr)
        sys.exit(1)

    if proc.returncode != 0:
        stderr_text = proc.stderr.decode("utf-8", errors="replace")
        if "CharNotPrinted" in stderr_text:
            # Expected when glyph is too wide for selected width: skip and replace
            return False, ""
        else:
            print(
                f"Error: Unexpected exit code {proc.returncode} for args: {args}\nStderr:\n{stderr_text}",
                file=sys.stderr,
            )
            sys.exit(1)

    try:
        out_str = proc.stdout.decode("utf-8")
    except UnicodeDecodeError as exc:
        print(f"Error: UTF-8 decoding error for args: {args}\n{exc}", file=sys.stderr)
        sys.exit(1)

    return True, out_str


def generate_dataset(
    output_path: pathlib.Path,
    target_count: int,
    dataset_name: str,
    seen_args: set,
    pyfiglet_dir: pathlib.Path,
    timeout_sec: float,
) -> int:
    """Generate target_count unique test cases into output_path as JSON Lines."""
    print(f"Starting generation of {target_count} cases for {dataset_name} ({output_path.name})...")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    count = 0
    start_time = time.time()

    with open(output_path, "w", encoding="utf-8") as f:
        while count < target_count:
            # Guarantee narrow right-to-left cases are included in both files
            force_narrow_rtl = (count % 5 == 0)

            args = generate_candidate(force_narrow_rtl=force_narrow_rtl)
            args_tuple = tuple(args)

            if args_tuple in seen_args:
                continue

            font_name, width, text_args = parse_candidate_args(args)
            if should_skip_glyph_width(font_name, width, text_args):
                # Avoid upstream wrapping loop when non-space glyph width == requested -w
                continue

            success, result = run_pyfiglet(args, pyfiglet_dir, timeout_sec)
            if not success:
                # CharNotPrinted or other failure: replace this candidate
                continue

            seen_args.add(args_tuple)
            record = {"args": args, "out": result}
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            f.flush()
            count += 1

            if count % 100 == 0 or count == target_count:
                elapsed = time.time() - start_time
                rate = count / elapsed if elapsed > 0 else 0
                print(f"[{dataset_name}] Progress: {count}/{target_count} cases generated ({rate:.1f} cases/s)")

    print(f"Finished {dataset_name}: {count} cases written to {output_path}")
    return count


def main():
    print(f"Pyfiglet directory:  {PYFIGLET_DIR}")
    print(f"Output directory:    {DATA_DIR}")
    print(f"Visible output file: {VISIBLE_FILE}")
    print(f"Hidden output file:  {HIDDEN_FILE}")

    if not PYFIGLET_DIR.exists():
        print(f"Error: Original pyfiglet checkout not found at {PYFIGLET_DIR}", file=sys.stderr)
        sys.exit(1)

    seen_args = set()

    # Generate visible.jsonl (2,000 cases)
    visible_count = generate_dataset(
        output_path=VISIBLE_FILE,
        target_count=TARGET_COUNT_PER_FILE,
        dataset_name="visible",
        seen_args=seen_args,
        pyfiglet_dir=PYFIGLET_DIR,
        timeout_sec=TIMEOUT_PER_CASE,
    )

    # Generate hidden.jsonl (2,000 cases, all unique from visible)
    hidden_count = generate_dataset(
        output_path=HIDDEN_FILE,
        target_count=TARGET_COUNT_PER_FILE,
        dataset_name="hidden",
        seen_args=seen_args,
        pyfiglet_dir=PYFIGLET_DIR,
        timeout_sec=TIMEOUT_PER_CASE,
    )

    print("\n" + "=" * 50)
    print("Generation Summary:")
    print(f"  Visible cases count: {visible_count} ({VISIBLE_FILE})")
    print(f"  Hidden cases count:  {hidden_count} ({HIDDEN_FILE})")
    print(f"  Total unique cases:  {len(seen_args)}")
    print("=" * 50)


if __name__ == "__main__":
    main()
