#!/usr/bin/env python3
"""
Step 4 test case generator for figlet-go.
Generates:
  tests/data/visible.jsonl (2000 cases)
  tests/data/hidden.jsonl  (2000 cases)
Using the sibling pyfiglet checkout as the ground-truth reference.
"""

import json
import os
import pathlib
import random
import subprocess
import sys
from collections import Counter

# -----------------------------------------------------------------------------
# Configuration and Path Resolution
# -----------------------------------------------------------------------------

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
TRACK2_DIR = REPO_ROOT.parent
PYFIGLET_DIR = TRACK2_DIR / "pyfiglet"
DATA_DIR = SCRIPT_DIR / "data"

VISIBLE_PATH = DATA_DIR / "visible.jsonl"
HIDDEN_PATH = DATA_DIR / "hidden.jsonl"

RANDOM_SEED = 7
TARGET_COUNT = 2000
MAX_ATTEMPTS_PER_SPLIT = 25000
TIMEOUT_SECONDS = 5

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

JUSTIFICATIONS = ["auto", "left", "center", "right"]

DIRECTIONS = ["auto", "left-to-right", "right-to-left"]

# -----------------------------------------------------------------------------
# Text Corpora & Generators
# -----------------------------------------------------------------------------

# Smushing pairs, hierarchy, and punctuation edge cases from NOTES.md
SMUSH_STRINGS = [
    # Equal characters
    "AA", "BB", "XX", "++", "--", "==", "**", "##", "::", "__", "oo", "99",
    # Lowline pairs with hierarchy characters
    "_|", "|_", "_/", "/_", "_\\", "\\_", "_[", "]_", "_{", "}_", "_(", ")_", "_<", ">_",
    # Hierarchy pairs (first match wins; later class replaces earlier class)
    "|/", "/|", "|\\", "\\|", "/[", "[/", "\\[", "[\\]", "\\{", "{\\",
    "[{", "{[", "{<", "<{", "(<", "<(", "|<>",
    # Pair smushing
    "[]", "][", "{}", "}{", "()", ")(", "[{()}]", "([{}])", "((()))", "[][][]",
    # Big-X pairs
    "/\\", "\\/", "><", "<>", "/\\/\\", "><><",
    # Mixed smushing expressions
    "|/\\_[]{}()<>", "/\\><_|", "[]{}()<>", "[-_-]", "{*_*}", "(o_O)", "\\o/",
    # Hardblank tests ($ is hardblank in standard fonts)
    "$$", "$A", "A$", "hello$world", "$ $", "$$$",
]

# Short words and tokens (vital for narrow widths like 10 and 20)
SHORT_TOKENS = [
    "A", "B", "I", "l", "1", "!", "?", "+", "-", "*", "/", "\\", "_",
    "Go", "Hi", "OK", "42", "7", "no", "up", "to", "in", "on", "it",
    "cat", "dog", "fox", "sun", "run", "bar", "foo", "baz", "yes",
    "[]", "{}", "()", "/\\", "><", "::", "--", "==", "++",
    "Ä", "Ö", "Ü", "ä", "ö", "ü", "ß",
]

# Normal words and multi-argument cases
WORDS_SINGLE = [
    "Go", "Hi", "OK", "42", "yes", "no", "cat", "dog", "fox", "sun", "run", "bar",
    "hello", "world", "figlet", "golang", "harbor", "source", "python", "format",
    "banner", "awesome", "terminal", "display", "render", "standard", "output", "stream",
    "CamelCase", "PascalCase", "snake_case", "kebab-case", "ALL_CAPS", "MixedCase",
]

WORDS_MULTI = [
    ["Hello", "World"],
    ["Go", "FIGlet"],
    ["quick", "brown", "fox"],
    ["step", "by", "step"],
    ["one", "two", "three"],
    ["test", "case", "suite"],
    ["left", "right", "center"],
    ["a", "b", "c"],
    ["foo", "bar", "baz"],
    ["1", "2", "3", "4", "5"],
    ["alpha", "beta", "gamma"],
]

# Whitespace edge cases (double spaces, leading/trailing spaces, space arguments)
WHITESPACE_CASES = [
    ["hello  world"],
    ["A  B"],
    ["double  spaces  test"],
    [" leading"],
    ["   wide"],
    ["trailing "],
    ["spaced   "],
    [" both "],
    [" "],
    ["   "],
    ["hello ", " world"],
    [" ", "middle", " "],
    ["a", " ", "b"],
    ["word   with   three   spaces"],
]

# Long sentences requiring wrapping across lines
LONG_SENTENCES = [
    ["The quick brown fox jumps over the lazy dog."],
    ["FIGlet creates large letters out of ordinary text."],
    ["Pure Go implementation of the Python pyfiglet CLI tool."],
    ["Testing line wrapping across narrow and wide column limits."],
    ["Short and long words combined in a single sentence for wrapping tests."],
    ["Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor."],
    ["To be, or not to be, that is the question: Whether tis nobler in the mind to suffer."],
    ["In computer programming, FIGlet is a program that generates text banners."],
    ["A long sentence designed to test repeated wrapping behavior across multiple lines."],
    ["Another sentence testing justified text layout across various width boundaries."],
]

# Long words without spaces (testing character-level wrap behavior)
LONG_WORDS = [
    ["Supercalifragilisticexpialidocious"],
    ["Antidisestablishmentarianism"],
    ["ABCDEFGHIJKLMNOPQRSTUVWXYZ"],
    ["abcdefghijklmnopqrstuvwxyz"],
    ["01234567890123456789"],
    ["----------------------------------------"],
    ["========================================"],
]

# Latin-1, German Umlaute, and characters absent from font
LATIN1_AND_EXTENDED = [
    ["ÄÖÜäöüß"],
    ["Grüße aus Köln"],
    ["Übergrößen"],
    ["Köpfe"],
    ["Café"],
    ["Señor"],
    ["naïve"],
    ["crème brûlée"],
    ["façade"],
    ["résumé"],
    ["áéíóú"],
    ["ñÑ"],
    ["çÇ"],
    ["Hello € world"],
    ["Test © 2026"],
    ["Symbols: ★ ♥ ♠"],
    ["Unicode: 漢字"],
    ["Emoji: 😀 🎉"],
]

# Flip and Reverse targeted strings
FLIP_REVERSE_CASES = [
    ["PRb"],
    ["bRP"],
    ["AVMW"],
    ["WMVA"],
    ["mw"],
    ["wm"],
    ["^v"],
    ["v^"],
    ["_ -"],
    ["(parentheses)"],
    ["[brackets]"],
    ["{braces}"],
    ["<angles>"],
    ["/slashes\\"],
    ["[(< /\\ >)]"],
    ["P(A)R [M] b{W} /v\\ ^_-"],
    ["Problem Report (b)"],
    ["Maximum Waves"],
]

VOCABULARY = [
    "alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta", "theta",
    "apple", "banana", "cherry", "date", "fig", "grape", "lemon", "mango",
    "red", "green", "blue", "yellow", "cyan", "magenta", "black", "white",
    "north", "south", "east", "west", "up", "down", "left", "right",
    "zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
    "cat", "dog", "bird", "fish", "lion", "tiger", "bear", "wolf", "fox",
    "code", "data", "test", "file", "line", "path", "node", "tree", "root",
]


def generate_candidate_text(rng: random.Random, width: int) -> list[str]:
    """
    Generate diverse text arguments according to requirement 5.
    If width is 10, biases toward short tokens so that narrow-width cases
    can succeed rather than being repeatedly rejected by CharNotPrinted.
    """
    if width == 10 and rng.random() < 0.65:
        # Pick 1-2 short tokens that can fit in 10 columns
        if rng.random() < 0.5:
            return [rng.choice(SHORT_TOKENS)]
        else:
            return [rng.choice(SHORT_TOKENS), rng.choice(SHORT_TOKENS)]

    category = rng.randint(0, 7)
    if category == 0:
        return [rng.choice(SMUSH_STRINGS)]
    elif category == 1:
        if rng.random() < 0.5:
            return [rng.choice(WORDS_SINGLE)]
        else:
            return list(rng.choice(WORDS_MULTI))
    elif category == 2:
        return list(rng.choice(WHITESPACE_CASES))
    elif category == 3:
        return list(rng.choice(LONG_SENTENCES))
    elif category == 4:
        return list(rng.choice(LONG_WORDS))
    elif category == 5:
        return list(rng.choice(LATIN1_AND_EXTENDED))
    elif category == 6:
        return list(rng.choice(FLIP_REVERSE_CASES))
    else:
        # Dynamic composite from vocabulary (1 to 4 words)
        num_words = rng.randint(1, 4)
        words = [rng.choice(VOCABULARY) for _ in range(num_words)]
        if rng.random() < 0.4:
            # Join into single string
            return [" ".join(words)]
        else:
            # Pass as separate CLI arguments
            return words


def generate_candidate_args(rng: random.Random) -> list[str]:
    """
    Produce a candidate CLI argument list.
    Options: -f, -w, -j, -D with independently enabled flags -r, -F, -s, -n.
    """
    font = rng.choice(FONTS)
    width = rng.choice(WIDTHS)
    justify = rng.choice(JUSTIFICATIONS)
    direction = rng.choice(DIRECTIONS)

    # Boolean flags enabled independently with probability 1/4
    flags = []
    if rng.random() < 0.25:
        flags.append("-r")
    if rng.random() < 0.25:
        flags.append("-F")
    if rng.random() < 0.25:
        flags.append("-s")
    if rng.random() < 0.25:
        flags.append("-n")

    text_tokens = generate_candidate_text(rng, width)

    args = [
        "-f", font,
        "-w", str(width),
        "-j", justify,
        "-D", direction,
    ] + flags + text_tokens

    return args


# -----------------------------------------------------------------------------
# Reference CLI Invocation
# -----------------------------------------------------------------------------

def run_reference_cli(ref_dir: pathlib.Path, args: list[str], timeout: int = 5) -> tuple[int, str, str]:
    """
    Execute [sys.executable, "-m", "pyfiglet", *args] strictly using the
    sibling checkout reference without shell=True.
    """
    cmd = [sys.executable, "-m", "pyfiglet"] + args
    env = dict(os.environ)
    env["PYTHONUTF8"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONPATH"] = str(ref_dir)

    try:
        proc = subprocess.run(
            cmd,
            cwd=str(ref_dir),
            env=env,
            capture_output=True,
            timeout=timeout,
            shell=False,
        )
        try:
            stdout_str = proc.stdout.decode("utf-8")
        except UnicodeDecodeError as err:
            return -2, "", f"UTF-8 decode error: {err}"

        stderr_str = proc.stderr.decode("utf-8", errors="replace")
        return proc.returncode, stdout_str, stderr_str

    except subprocess.TimeoutExpired:
        return -1, "", f"Timeout after {timeout} seconds"


# -----------------------------------------------------------------------------
# Split Generation & Summary
# -----------------------------------------------------------------------------

def generate_split(
    split_name: str,
    target_count: int,
    rng: random.Random,
    global_seen_args: set[tuple[str, ...]],
    ref_dir: pathlib.Path,
) -> tuple[list[dict], dict]:
    """
    Generate target_count unique, valid cases for a split.
    """
    cases: list[dict] = []
    split_seen_args: set[tuple[str, ...]] = set()

    rejections = {
        "timeout": 0,
        "nonzero": 0,
        "decode_error": 0,
        "duplicate": 0,
        "samples": [],
    }

    attempts = 0
    print(f"Generating {split_name} ({target_count} cases)...")

    while len(cases) < target_count:
        attempts += 1
        if attempts > MAX_ATTEMPTS_PER_SPLIT:
            raise RuntimeError(
                f"Exceeded maximum attempts ({MAX_ATTEMPTS_PER_SPLIT}) for {split_name}. "
                f"Only generated {len(cases)}/{target_count} valid cases."
            )

        args = generate_candidate_args(rng)
        args_key = tuple(args)

        if args_key in global_seen_args or args_key in split_seen_args:
            rejections["duplicate"] += 1
            continue

        returncode, stdout_str, stderr_str = run_reference_cli(ref_dir, args, timeout=TIMEOUT_SECONDS)

        if returncode != 0:
            if returncode == -1:
                rejections["timeout"] += 1
                reason = "TimeoutExpired (>5s)"
            elif returncode == -2:
                rejections["decode_error"] += 1
                reason = "UnicodeDecodeError"
            else:
                rejections["nonzero"] += 1
                reason = f"Nonzero exit ({returncode})"

            if len(rejections["samples"]) < 5:
                rejections["samples"].append({
                    "args": args,
                    "reason": reason,
                    "stderr": stderr_str.strip()[:200],
                })
            continue

        # Valid result: store exact output without altering whitespace
        cases.append({"args": args, "out": stdout_str})
        split_seen_args.add(args_key)
        global_seen_args.add(args_key)

        if len(cases) % 250 == 0 or len(cases) == target_count:
            print(f"  [{split_name}] {len(cases)}/{target_count} cases generated (attempts: {attempts})...")

    rejections["total_attempts"] = attempts
    return cases, rejections


def analyze_split(cases: list[dict]) -> dict:
    """
    Compute distributions and counts for the summary report.
    """
    fonts = Counter()
    widths = Counter()
    justifications = Counter()
    directions = Counter()
    flag_r = 0
    flag_F = 0
    flag_s = 0
    flag_n = 0
    both_sn = 0
    rtl_narrow = 0

    for item in cases:
        args = item["args"]
        if "-f" in args:
            fonts[args[args.index("-f") + 1]] += 1
        if "-w" in args:
            w_val = int(args[args.index("-w") + 1])
            widths[w_val] += 1
        else:
            w_val = 80
        if "-j" in args:
            justifications[args[args.index("-j") + 1]] += 1
        if "-D" in args:
            d_val = args[args.index("-D") + 1]
            directions[d_val] += 1
        else:
            d_val = "auto"

        has_r = "-r" in args
        has_F = "-F" in args
        has_s = "-s" in args
        has_n = "-n" in args

        if has_r:
            flag_r += 1
        if has_F:
            flag_F += 1
        if has_s:
            flag_s += 1
        if has_n:
            flag_n += 1
        if has_s and has_n:
            both_sn += 1
        if d_val == "right-to-left" and w_val in (10, 20):
            rtl_narrow += 1

    return {
        "count": len(cases),
        "fonts": fonts,
        "widths": widths,
        "justifications": justifications,
        "directions": directions,
        "flag_r": flag_r,
        "flag_F": flag_F,
        "flag_s": flag_s,
        "flag_n": flag_n,
        "both_sn": both_sn,
        "rtl_narrow": rtl_narrow,
    }


def print_split_summary(name: str, stats: dict, rejections: dict):
    count = stats["count"]
    print("=" * 60)
    print(f"Summary for {name} ({count} cases):")
    print("=" * 60)
    print("Fonts:")
    for k in FONTS:
        v = stats["fonts"].get(k, 0)
        pct = (v / count * 100) if count else 0
        print(f"  {k:12s}: {v:4d} ({pct:5.1f}%)")
    print("Widths:")
    for k in sorted(WIDTHS):
        v = stats["widths"].get(k, 0)
        pct = (v / count * 100) if count else 0
        print(f"  {k:3d}:         {v:4d} ({pct:5.1f}%)")
    print("Justifications:")
    for k in JUSTIFICATIONS:
        v = stats["justifications"].get(k, 0)
        pct = (v / count * 100) if count else 0
        print(f"  {k:12s}: {v:4d} ({pct:5.1f}%)")
    print("Directions:")
    for k in DIRECTIONS:
        v = stats["directions"].get(k, 0)
        pct = (v / count * 100) if count else 0
        print(f"  {k:15s}: {v:4d} ({pct:5.1f}%)")
    print("Boolean Flags:")
    print(f"  -r:             {stats['flag_r']:4d} ({stats['flag_r']/count*100:5.1f}%)")
    print(f"  -F:             {stats['flag_F']:4d} ({stats['flag_F']/count*100:5.1f}%)")
    print(f"  -s:             {stats['flag_s']:4d} ({stats['flag_s']/count*100:5.1f}%)")
    print(f"  -n:             {stats['flag_n']:4d} ({stats['flag_n']/count*100:5.1f}%)")
    print(f"  Both -s and -n: {stats['both_sn']:4d} ({stats['both_sn']/count*100:5.1f}%)")
    print(f"RTL + Narrow (10 or 20): {stats['rtl_narrow']:4d} ({stats['rtl_narrow']/count*100:5.1f}%)")
    print("Rejection Statistics:")
    print(f"  Total attempts:  {rejections['total_attempts']}")
    print(f"  Nonzero exits:   {rejections['nonzero']}")
    print(f"  Timeouts (>5s):  {rejections['timeout']}")
    print(f"  Duplicates:      {rejections['duplicate']}")
    if rejections["samples"]:
        print("  Diagnostic rejection examples:")
        for s in rejections["samples"]:
            print(f"    - args: {s['args']}")
            print(f"      reason: {s['reason']}; stderr: {s['stderr']}")
    print()


# -----------------------------------------------------------------------------
# Main Entry Point
# -----------------------------------------------------------------------------

def main():
    print(f"Reference pyfiglet repository: {PYFIGLET_DIR}")
    if not (PYFIGLET_DIR / "pyfiglet" / "__init__.py").exists():
        raise RuntimeError(f"Could not locate reference pyfiglet at: {PYFIGLET_DIR}")

    random.seed(RANDOM_SEED)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    tmp_visible_path = DATA_DIR / "visible.jsonl.tmp"
    tmp_hidden_path = DATA_DIR / "hidden.jsonl.tmp"

    global_seen_args: set[tuple[str, ...]] = set()

    # Generate visible split
    visible_cases, visible_rejections = generate_split(
        "visible", TARGET_COUNT, random, global_seen_args, PYFIGLET_DIR
    )

    # Generate hidden split (zero overlap with visible guaranteed by global_seen_args)
    hidden_cases, hidden_rejections = generate_split(
        "hidden", TARGET_COUNT, random, global_seen_args, PYFIGLET_DIR
    )

    # Validate constraints
    assert len(visible_cases) == TARGET_COUNT, f"Visible count {len(visible_cases)} != {TARGET_COUNT}"
    assert len(hidden_cases) == TARGET_COUNT, f"Hidden count {len(hidden_cases)} != {TARGET_COUNT}"

    visible_set = set(tuple(c["args"]) for c in visible_cases)
    hidden_set = set(tuple(c["args"]) for c in hidden_cases)
    assert len(visible_set) == TARGET_COUNT, "Duplicate args found within visible split"
    assert len(hidden_set) == TARGET_COUNT, "Duplicate args found within hidden split"
    overlap = len(visible_set.intersection(hidden_set))
    assert overlap == 0, f"Overlap detected between visible and hidden: {overlap} cases"

    # Write temporary files using stable serialization and LF line endings
    print("Writing temporary files...")
    with open(tmp_visible_path, "w", encoding="utf-8", newline="\n") as f:
        for item in visible_cases:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    with open(tmp_hidden_path, "w", encoding="utf-8", newline="\n") as f:
        for item in hidden_cases:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    # Atomically replace final files
    os.replace(tmp_visible_path, VISIBLE_PATH)
    os.replace(tmp_hidden_path, HIDDEN_PATH)
    print(f"Saved: {VISIBLE_PATH}")
    print(f"Saved: {HIDDEN_PATH}")
    print()

    # Print summaries
    vis_stats = analyze_split(visible_cases)
    hid_stats = analyze_split(hidden_cases)

    print_split_summary("Visible Split", vis_stats, visible_rejections)
    print_split_summary("Hidden Split", hid_stats, hidden_rejections)

    print(f"Final Validation:")
    print(f"  Visible / Hidden args overlap: {overlap} (PASSED)")
    print("Generation completed successfully.")


if __name__ == "__main__":
    main()
