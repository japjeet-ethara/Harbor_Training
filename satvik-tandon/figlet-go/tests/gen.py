#!/usr/bin/env python3
"""Generate frozen cases from the pinned pyfiglet source beside this task."""
import json
import random
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = ROOT.parent / "pyfiglet"
FONTS = ["standard", "slant", "small", "big", "mini", "banner", "shadow", "script"]
WIDTHS = [10, 20, 40, 60, 80, 120]
JUSTIFY = ["auto", "left", "center", "right"]
DIRECTIONS = ["auto", "left-to-right", "right-to-left"]
TEXTS = [
    "hello", "FIGlet", "| / \\ _ [ ] { } ( ) < >", "two  spaces",
    "a long sentence that must wrap around a narrow terminal window",
    "café Straße niño", "~ ` ^", "smush |_|", "go touch grass",
    "[{}] (<>)/\\_||", "é ß ñ", "missing glyph: 漢字",
]

def candidate(rng):
    args = ["-f", rng.choice(FONTS), "-w", str(rng.choice(WIDTHS)),
            "-j", rng.choice(JUSTIFY), "-D", rng.choice(DIRECTIONS)]
    for flag in ("-r", "-F", "-s", "-n"):
        if rng.randrange(4) == 0:
            args.append(flag)
    args.append(rng.choice(TEXTS))
    return args

def render(pyfiglet, args, timeout=1.0):
    try:
        result = subprocess.run(
            [sys.executable, str(Path(__file__).with_name("render_main.py")),
             str(ORIGINAL), json.dumps(args, ensure_ascii=False)],
            capture_output=True, timeout=timeout, check=False,
        )
    except subprocess.TimeoutExpired:
        return None
    if result.returncode != 0:
        return None
    try:
        return result.stdout.decode("utf-8")
    except UnicodeDecodeError:
        return None

def generate(path, rng, seen, pyfiglet, count=2000):
    accepted = 0
    attempts = 0
    with path.open("w", encoding="utf-8", newline="\n") as out:
        while accepted < count:
            attempts += 1
            if attempts > count * 20:
                raise RuntimeError(f"could not collect {count} valid unique cases for {path.name}")
            args = candidate(rng)
            key = tuple(args)
            if key in seen:
                continue
            result = render(pyfiglet, args)
            if result is None:
                continue
            # Windows translates text-mode stdout newlines to CRLF. Harbor
            # runs on Linux, where the original emits LF; canonicalize the
            # captured bytes to the source program's logical output lines.
            result = result.replace("\r\n", "\n")
            seen.add(key)
            out.write(json.dumps({"args": args, "out": result}, ensure_ascii=False) + "\n")
            accepted += 1
            if accepted % 250 == 0:
                print(f"{path.name}: {accepted}/{count} (tried {attempts})", flush=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--pyfiglet", type=Path, default=ORIGINAL,
                        help="path to cloned pyfiglet repository (default: sibling ../pyfiglet)")
    options = parser.parse_args()
    source = options.pyfiglet.resolve()
    sys.path.insert(0, str(source))
    import pyfiglet
    rng = random.Random(7)
    data = ROOT / "tests" / "data"
    data.mkdir(parents=True, exist_ok=True)
    seen = set()
    generate(data / "visible.jsonl", rng, seen, pyfiglet)
    generate(data / "hidden.jsonl", rng, seen, pyfiglet)
