#!/usr/bin/env python3
"""Generate visible.jsonl and hidden.jsonl for the FIGlet Harbor task.

Run from the task folder (figlet-go/) with the pyfiglet clone next to it:
    python tests/gen.py

Uses subprocess to call pyfiglet for each case to avoid memory issues.
"""

import json
import random
import subprocess
import sys
from pathlib import Path

random.seed(7)

TASK_DIR = Path(__file__).resolve().parent.parent
PYFIGLET_DIR = TASK_DIR.parent / "pyfiglet"

FONTS = ("standard", "slant", "small", "big", "mini", "banner", "shadow", "script")
WIDTHS = (10, 20, 40, 60, 80, 120)
JUSTIFICATIONS = ("auto", "left", "center", "right")
DIRECTIONS = ("auto", "left-to-right", "right-to-left")

TEXTS = [
    "hello",
    "world",
    "figlet",
    "Go program",
    "a  b",
    "/\\",
    "||",
    "[]{}()<>",
    "_ | / \\ [ ] { } ( ) < >",
    "/ + \\",
    "\\ + /",
    "> + <",
    "hardblank",
    "A B C",
    "one two three",
    "wrap this sentence across several narrow lines",
    "A long sentence that forces wrapping at small widths.",
    "The quick brown fox jumps over the lazy dog.",
    "\u00e9 \u00df \u00f1",
    "caf\u00e9 ma\u00f1ana stra\u00dfe",
    "\u6771\u4eac",
    "\u2603",
    "\u00a9 \u00ae \u2122",
    "12345 !?.,",
    "leading and trailing ",
    "  multiple leading spaces",
    "|_|",
    "X Y Z",
    "abc",
    "HELLO WORLD",
]

NARROW_TEXTS = [
    "hello", "world", "figlet", "ab", "/\\", "||",
    "A B", "> <", "hi", "Go", "XY", "|_|",
]

PYTHON = sys.executable


def run_pyfiglet(args: list[str]) -> str | None:
    """Run pyfiglet with the given CLI args and return stdout, or None on error."""
    cmd = [PYTHON, "-m", "pyfiglet"] + args
    try:
        r = subprocess.run(
            cmd,
            capture_output=True,
            timeout=10,
            cwd=str(PYFIGLET_DIR),
        )
        if r.returncode != 0:
            return None
        # Return raw bytes decoded as utf-8
        return r.stdout.decode("utf-8", errors="replace")
    except (subprocess.TimeoutExpired, Exception):
        return None


def make_args() -> list[str]:
    """Generate random pyfiglet CLI arguments."""
    font = random.choice(FONTS)
    width = random.choice(WIDTHS)
    justify = random.choice(JUSTIFICATIONS)
    direction = random.choice(DIRECTIONS)

    if font in ("big", "banner", "shadow", "script") and width < 40:
        width = random.choice((40, 60, 80, 120))

    args = ["-f", font, "-w", str(width), "-j", justify, "-D", direction]

    for flag in ("-r", "-F", "-s", "-n"):
        if random.random() < 0.25:
            args.append(flag)

    text = random.choice(NARROW_TEXTS if width <= 20 else TEXTS)
    args.append(text)
    return args


def generate(path: Path, count: int, used: set):
    path.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    rejected = 0

    with path.open("w", encoding="utf-8", newline="\n") as f:
        while written < count:
            args = make_args()
            key = tuple(args)
            if key in used:
                continue

            out = run_pyfiglet(args)
            if out is None:
                rejected += 1
                continue

            used.add(key)
            record = {"args": args, "out": out}
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            written += 1

            if written % 100 == 0:
                print(
                    f"  {path.name}: {written}/{count} ({rejected} skipped)",
                    flush=True,
                )

    print(
        f"  {path.name}: {written}/{count} done ({rejected} total skipped)",
        flush=True,
    )


def main():
    used: set = set()
    data_dir = TASK_DIR / "tests" / "data"

    print("Generating visible.jsonl ...")
    generate(data_dir / "visible.jsonl", 2000, used)

    print("Generating hidden.jsonl ...")
    generate(data_dir / "hidden.jsonl", 2000, used)

    print("All done!")


if __name__ == "__main__":
    main()
