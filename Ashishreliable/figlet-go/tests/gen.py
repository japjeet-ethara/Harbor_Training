#!/usr/bin/env python3
"""Generate visible and hidden FIGlet cases from the original pyfiglet.

Run this on the laptop, from anywhere:

    python tests/gen.py

It expects the pyfiglet checkout from Step 1 to be next to the task folder,
with pyfiglet/fonts/ already populated (the Makefile setup step).

Every "out" value comes from running the original pyfiglet main() with the
case's argv and capturing stdout. Nothing in this file writes an answer by
hand.
"""

import io
import json
import random
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve()
TASK_DIR = HERE.parents[1]
PROJECT_DIR = HERE.parents[2]
REPO_DIR = PROJECT_DIR / "pyfiglet"
DATA_DIR = TASK_DIR / "tests" / "data"

FONTS = ["standard", "slant", "small", "big", "mini", "banner", "shadow", "script"]
WIDTHS = [10, 20, 40, 60, 80, 120]
JUSTIFIES = ["auto", "left", "center", "right"]
DIRECTIONS = ["auto", "left-to-right", "right-to-left"]

NORMAL = [
    "hello", "world", "figlet", "harbor", "Go", "test", "quick", "brown",
    "fox", "jumps", "over", "lazy", "dog", "abc", "XYZ", "123", "Hello",
    "World", "ASCII", "art", "title", "code", "build", "agent", "player",
    "font", "render", "smush", "kerning", "left", "right", "center",
    "mirror", "flip", "strip", "normalize", "the", "and", "of", "a", "to",
    "in", "is", "it", "that", "for", "you", "was", "with", "on", "are",
    "as", "at", "be", "this", "have", "from", "or", "one", "had", "by",
    "word", "but", "not", "what", "all", "were", "we", "when", "your",
    "can", "said", "there", "use", "an", "each", "which", "she", "do",
    "how", "their", "if", "will", "up", "other", "about", "out", "many",
    "then", "them", "these", "so", "some", "her", "would", "make", "like",
    "him", "into", "time", "has", "look", "two", "more", "write", "go",
    "see", "number", "no", "way", "could", "people", "my", "than", "first",
    "water", "been", "call", "who", "oil", "its", "now", "find", "long",
    "down", "day", "did", "get", "come", "made", "may", "part",
]

TRICKY = [
    "||", "| |", "_/", "/_", "|/", "/|", "[{", "}]", "[]", "{}", "()",
    "<>", "/\\", "\\/", "><", "$$", "_", "|", "/", "\\", "[", "]", "{",
    "}", "(", ")", "<", ">", "|_|", "[]{}()<>", "|/\\_[]{}()<>", "a|b",
    "a/b\\c_d[e]f{g}h(i)<j>", "__/\\__", "[](){}<>", "|/-\\", "><><",
    "[[{{(())}}]]", "||_||", "$$$$", "___", "///", "\\\\", "a_b_c",
    "x/y/z", "left/right", "a+b=c", "1|2|3", "no-op", "under_score",
    "back\\slash", "[]{}", "()<>", "|/\\|", "][", "}{", ")(",
]

LATIN = [
    "café", "straße", "mañana", "ÄÖÜäöüß", "é ß ñ", "naïve", "résumé",
    "piñata", "über", "Grüße", "Ça va", "señor", "François", "déjà vu",
    "München", "café au lait", "élève", "garçon", "über alles",
    "smörgåsbord", "ÆØÅ", "æøå", "ÐðÞþ", "£€¥", "©®™", "°±²³", "µ¶·",
    "¼½¾", "¿¡", "«»", "×÷", "àéîõü", "ÀÉÎÕÜ", "çñ", "œŒ", "šž",
]

MISSING = [
    "→λ漢🙂", "snowman ☃", "emoji 🙂 test", "日本語", "Ω≈ç√", "★☆",
    "→←↑↓", "♠♣♥♦", "☀☁☂", "😀😃😄", "𝄞", "ﬁﬂ", "①②③", "αβγδε",
    "Привет", "שלום", "مرحبا", "हिन्दी", "ไทย", "한국어", "x🙂y",
    "🙂🙂🙂", "tab\there", "zero\u200bwidth", "nbsp\u00a0here",
    "line\u2028separator", "☃☃☃", "x★y", "a→b", "λx",
]

LONG = [
    "the quick brown fox jumps over the lazy dog",
    "the quick brown fox jumps over the lazy dog and keeps running through the forest until it reaches the river",
    "a long sentence that must wrap because it is much wider than the narrow terminal window",
    "pack my box with five dozen liquor jugs",
    "how vexingly quick daft zebras jump",
    "sphinx of black quartz judge my vow",
    "the five boxing wizards jump quickly",
    "jackdaws love my big sphinx of quartz",
    "we promptly judged antique ivory buckles for the next prize",
    "a very long title with many words that will certainly need to wrap at small widths and maybe even at eighty columns",
    "one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen",
    "supercalifragilisticexpialidocious",
    "antidisestablishmentarianism",
    "pneumonoultramicroscopicsilicovolcanoconiosis",
    "the rain in spain stays mainly in the plain",
    "all work and no play makes jack a dull boy",
    "to be or not to be that is the question",
    "it was the best of times it was the worst of times",
    "call me ishmael some years ago never mind how long precisely",
    "in the beginning god created the heavens and the earth",
]

NEWLINE = [
    "line one\nline two",
    "a\nb",
    "hello\nworld\nagain",
    "top\n\nbottom",
    "\nleading",
    "trailing\n",
    "a\n\n\nb",
    "first line\nsecond line\nthird line",
    "wrap\nthis\nnow",
    "x\ny",
]

KINDS = [
    "normal", "normal", "normal",
    "tricky", "tricky", "tricky",
    "latin", "latin",
    "missing", "missing",
    "long", "long",
    "newline",
    "symbols", "symbols",
    "double_space",
    "padded",
    "blank",
]


class Capture:
    """A stdout stand-in whose detach() gives main() a binary buffer."""

    def __init__(self):
        self.buffer = io.BytesIO()

    def write(self, data):
        if isinstance(data, str):
            data = data.encode("utf-8")
        return self.buffer.write(data)

    def flush(self):
        pass

    def detach(self):
        return self.buffer


def load_pyfiglet():
    fonts_dir = REPO_DIR / "pyfiglet" / "fonts"
    if not fonts_dir.is_dir():
        raise SystemExit(
            "missing %s\nRun the Step 1 font setup first:\n"
            "  mkdir -p pyfiglet/fonts && cp pyfiglet/fonts-standard/* pyfiglet/fonts/"
            % fonts_dir
        )
    missing = [f for f in FONTS if not (fonts_dir / (f + ".flf")).is_file()]
    if missing:
        raise SystemExit("missing font files in %s: %s" % (fonts_dir, ", ".join(missing)))

    sys.path.insert(0, str(REPO_DIR))
    import pyfiglet

    return pyfiglet


def render(pyfiglet, args):
    """Run the original main() with args and return its exact UTF-8 stdout."""
    old_argv = sys.argv
    old_stdout = sys.stdout
    capture = Capture()
    sys.argv = ["pyfiglet"] + args
    sys.stdout = capture
    try:
        rc = pyfiglet.main()
        data = capture.buffer.getvalue()
        if rc != 0:
            return None
        return data.decode("utf-8")
    except Exception:
        return None
    finally:
        sys.argv = old_argv
        sys.stdout = old_stdout


def random_symbols():
    alphabet = "|/\\_[]{}()<>"
    text = "".join(random.choice(alphabet) for _ in range(random.randint(2, 16)))
    if random.random() < 0.35:
        at = random.randrange(len(text) + 1)
        text = text[:at] + random.choice(NORMAL) + text[at:]
    return text


def make_text():
    kind = random.choice(KINDS)
    if kind == "normal":
        return random.choice(NORMAL), kind
    if kind == "tricky":
        return random.choice(TRICKY), kind
    if kind == "latin":
        return random.choice(LATIN), kind
    if kind == "missing":
        return random.choice(MISSING), kind
    if kind == "long":
        return random.choice(LONG), kind
    if kind == "newline":
        return random.choice(NEWLINE), kind
    if kind == "symbols":
        return random_symbols(), kind
    if kind == "double_space":
        return random.choice(NORMAL) + random.choice(["  ", "   "]) + random.choice(NORMAL), kind
    if kind == "padded":
        return "  " + random.choice(NORMAL) + "  ", kind
    if kind == "blank":
        return random.choice(["", " ", "   ", "\t"]), kind
    raise AssertionError(kind)


def make_case():
    font = None if random.random() < 0.10 else random.choice(FONTS)
    width = None if random.random() < 0.10 else random.choice(WIDTHS)
    justify = None if random.random() < 0.10 else random.choice(JUSTIFIES)
    direction = None if random.random() < 0.10 else random.choice(DIRECTIONS)
    reverse = random.random() < 0.25
    flip = random.random() < 0.25
    strip = random.random() < 0.25
    normalize = random.random() < 0.25

    # pyfiglet loops forever when a glyph is exactly as wide as the terminal.
    # Every font except mini has glyphs 10 columns wide, so width 10 uses mini
    # (max glyph width 8). Width 20 and above are safe for every listed font.
    if width == 10:
        font = "mini"

    text, kind = make_text()
    args = []
    if font is not None:
        args += ["-f", font]
    if width is not None:
        args += ["-w", str(width)]
    if justify is not None:
        args += ["-j", justify]
    if direction is not None:
        args += ["-D", direction]
    if reverse:
        args.append("-r")
    if flip:
        args.append("-F")
    if strip:
        args.append("-s")
    if normalize:
        args.append("-n")

    if kind in ("normal", "long") and " " in text and random.random() < 0.5:
        args.extend(text.split(" "))
    else:
        args.append(text)

    return args


def build_dataset(pyfiglet, count, seen):
    cases = []
    attempts = 0
    limit = count * 50
    while len(cases) < count:
        attempts += 1
        if attempts > limit:
            raise SystemExit("could not build %d valid cases after %d attempts" % (count, attempts))
        args = make_case()
        key = json.dumps(args, ensure_ascii=False)
        if key in seen:
            continue
        out = render(pyfiglet, args)
        if out is None:
            continue
        seen.add(key)
        cases.append({"args": args, "out": out})
    return cases, attempts


def stats(cases):
    c = Counter()
    for case in cases:
        args = case["args"]
        c["cases"] += 1
        if "-r" in args:
            c["-r"] += 1
        if "-F" in args:
            c["-F"] += 1
        if "-s" in args:
            c["-s"] += 1
        if "-n" in args:
            c["-n"] += 1
        c["font:" + (args[args.index("-f") + 1] if "-f" in args else "standard(default)")] += 1
        c["width:" + (args[args.index("-w") + 1] if "-w" in args else "80(default)")] += 1
        c["justify:" + (args[args.index("-j") + 1] if "-j" in args else "auto(default)")] += 1
        c["direction:" + (args[args.index("-D") + 1] if "-D" in args else "auto(default)")] += 1
    return c


def write_jsonl(path, cases):
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for case in cases:
            handle.write(json.dumps(case, ensure_ascii=False) + "\n")


def print_stats(name, c):
    print("%s: %d cases" % (name, c["cases"]))
    for group in ("font", "width", "justify", "direction"):
        items = sorted((k.split(":", 1)[1], v) for k, v in c.items() if k.startswith(group + ":"))
        print("  %-9s %s" % (group + ":", ", ".join("%s=%d" % item for item in items)))
    print("  flags:     -r=%d -F=%d -s=%d -n=%d" % (c["-r"], c["-F"], c["-s"], c["-n"]))


def main():
    random.seed(7)
    pyfiglet = load_pyfiglet()
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    seen = set()
    visible, visible_attempts = build_dataset(pyfiglet, 2000, seen)
    hidden, hidden_attempts = build_dataset(pyfiglet, 2000, seen)

    write_jsonl(DATA_DIR / "visible.jsonl", visible)
    write_jsonl(DATA_DIR / "hidden.jsonl", hidden)

    print("wrote %s" % (DATA_DIR / "visible.jsonl"))
    print("wrote %s" % (DATA_DIR / "hidden.jsonl"))
    print("attempts: visible=%d hidden=%d" % (visible_attempts, hidden_attempts))
    print_stats("visible", stats(visible))
    print_stats("hidden", stats(hidden))


if __name__ == "__main__":
    main()
