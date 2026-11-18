"""Make the visible and hidden answer files for the figlet-go task.

Runs on the author's laptop (NOT in Docker), with the pyfiglet folder from
Step 1 (fonts already set up) next to the task folder:

    harbor-practice/
        pyfiglet/      <- git clone + checkout 255827e + cp fonts-standard/* fonts/
        figlet-go/     <- this task

Run from the figlet-go folder:

    uv run --no-project --python 3.12 python tests/gen.py

Writes (one JSON object per line: {"args": [...], "out": "..."}):
    tests/data/visible.jsonl   2000 cases
    tests/data/hidden.jsonl    2000 different cases (the grader uses these)
    cheat/visible.jsonl        copy of the visible file, for the Step 7 cheat

Every "out" is the exact stdout of the ORIGINAL `python -m pyfiglet <args>`.
Never write an "out" by hand.

Cases are left out when pyfiglet crashes (CharNotPrinted on narrow widths),
hangs (some narrow widths loop forever), or prints only whitespace. A
program that prints nothing must never get a case right for free.
"""

import json
import os
import random
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

TASK = Path(__file__).resolve().parent.parent
PYFIGLET = TASK.parent / "pyfiglet"
N = 2000
TIMEOUT = 5

FONTS = ["standard", "slant", "small", "big", "mini", "banner", "shadow", "script"]
WIDTHS = [10, 20, 40, 60, 80, 120]
JUSTIFY = ["auto", "left", "center", "right"]
DIRECTION = ["auto", "left-to-right", "right-to-left"]

WORDS = """hello world figlet go port giant letters shout chat python twin exam
harbor task agent hidden smush kern wrap center right left mirror flip test
quick brown fox jumps over lazy dog alpha beta gamma delta omega zero one two
three 42 2026 v1.2 A-Z a+b x*y foo_bar end! why? yes: no; ok. (hi) [box]
{set} <tag> 100% #1 @home $5 ~tilde ^caret 'q' "dq" a=b c&d""".split()

# Rare cases from NOTES.md, plus the brackets and slashes every rule touches.
TRICKY = ["|", "/", "\\", "_", "[", "]", "{", "}", "(", ")", "<", ">",
          "|_|", "/\\", "\\/", "><", "<>", "[]", "{}", "()", "__", "||", "//",
          "\\\\", "_|_", "|/", "/[", "[{", "{(", "(<", "[)", "}{", ")(", "$",
          "$$", "a$b", "/_\\", "\\_/", "<|>", "{[()]}", "x/y\\z"]
LATIN1 = ["é", "ß", "ñ", "Ä", "Ö", "Ü", "ä", "ö", "ü", "café", "straße",
          "niño", "Ärger", "Öl", "Über", "ÿ", "Ç", "ø", "Å"]
MISSING = ["€", "中", "☃", "→", "\t", "Ω", "😀", "ǅ"]
SENTENCES = [
    "the quick brown fox jumps over the lazy dog",
    "pack my box with five dozen liquor jugs",
    "every smushing rule has to be copied exactly space for space",
    "a twin that is right on hello can be wrong on |_| in a narrow window",
    "hello world from the giant letter machine",
]


def make_text(rng: random.Random) -> list[str]:
    """Return the text part of the command line (one or more arguments)."""
    r = rng.random()
    if r < 0.15:
        text = rng.choice(SENTENCES)                       # long: must wrap
    elif r < 0.20:
        text = rng.choice(SENTENCES) + " " + rng.choice(SENTENCES)
    else:
        parts = []
        for _ in range(rng.choice([1, 1, 1, 2, 2, 3, 4])):
            p = rng.random()
            if p < 0.45:
                w = rng.choice(WORDS)
            elif p < 0.75:
                w = rng.choice(TRICKY)
            elif p < 0.88:
                w = rng.choice(LATIN1)
            else:
                w = rng.choice(WORDS) + rng.choice(MISSING)
            if rng.random() < 0.15:
                w = w.upper()
            parts.append(w)
        sep = rng.choice([" "] * 6 + ["  ", "   "])           # double spaces
        text = sep.join(parts)
    if rng.random() < 0.03:
        text = text.replace(" ", "\n", 1)                   # explicit newline
    if rng.random() < 0.04:
        text = " " + text
    if rng.random() < 0.04:
        text = text + " "
    # pyfiglet joins all text arguments with one space; sometimes pass the
    # words as separate arguments to test that.
    if rng.random() < 0.25 and " " in text.strip():
        args = [a for a in text.split(" ") if a]
    else:
        args = [text]
    # optparse would read an argument starting with "-" as an option.
    if any(a.startswith("-") for a in args):
        args = ["x" + a for a in args]
    return args


def make_case(rng: random.Random) -> list[str]:
    opts: list[list[str]] = []
    if rng.random() < 0.9:
        opts.append(["-f", rng.choice(FONTS)])
    if rng.random() < 0.85:
        opts.append(["-w", str(rng.choice(WIDTHS))])
    if rng.random() < 0.75:
        opts.append(["-j", rng.choice(JUSTIFY)])
    if rng.random() < 0.75:
        opts.append(["-D", rng.choice(DIRECTION)])
    for flag in ["-r", "-F", "-s", "-n"]:
        if rng.random() < 0.25:
            opts.append([flag])
    rng.shuffle(opts)
    return [a for o in opts for a in o] + make_text(rng)


def run_pyfiglet(args: list[str], cwd: str) -> str | None:
    env = dict(os.environ, PYTHONPATH=str(PYFIGLET), PYTHONIOENCODING="utf-8")
    try:
        p = subprocess.run([sys.executable, "-m", "pyfiglet", *args], cwd=cwd, env=env,
                           capture_output=True, timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        return None                                         # pyfiglet loops forever
    if p.returncode != 0 or not p.stdout.strip():
        return None                                         # crash or blank output
    return p.stdout.decode("utf-8")


def main() -> None:
    if not (PYFIGLET / "pyfiglet" / "fonts" / "standard.flf").is_file():
        sys.exit(f"Set up pyfiglet first: {PYFIGLET} with pyfiglet/fonts/ (Step 1).")
    rng = random.Random(7)
    seen: set[tuple[str, ...]] = set()
    sets: list[list[dict]] = [[], []]
    cwd = tempfile.mkdtemp()                                # no stray ./*.flf
    try:
        with ThreadPoolExecutor(max_workers=8) as pool:
            for k in (0, 1):
                while len(sets[k]) < N:
                    batch = []
                    while len(batch) < 400:
                        args = make_case(rng)
                        if tuple(args) not in seen:
                            seen.add(tuple(args))
                            batch.append(args)
                    outs = list(pool.map(lambda a: run_pyfiglet(a, cwd), batch))
                    for args, out in zip(batch, outs):
                        if out is not None and len(sets[k]) < N:
                            sets[k].append({"args": args, "out": out})
    finally:
        shutil.rmtree(cwd, ignore_errors=True)

    data = TASK / "tests" / "data"
    data.mkdir(parents=True, exist_ok=True)
    for name, cases in (("visible.jsonl", sets[0]), ("hidden.jsonl", sets[1])):
        with open(data / name, "w", encoding="utf-8", newline="\n") as f:
            for c in cases:
                f.write(json.dumps(c, ensure_ascii=True) + "\n")
    (TASK / "cheat").mkdir(exist_ok=True)
    shutil.copyfile(data / "visible.jsonl", TASK / "cheat" / "visible.jsonl")
    print(f"wrote {N} visible + {N} hidden cases ({len(seen)} tried)")


if __name__ == "__main__":
    main()
