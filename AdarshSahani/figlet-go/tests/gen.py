#!/usr/bin/env python3
"""Generate deterministic FIGlet output corpora using the original pyfiglet."""

import json
import random
import sys
from functools import lru_cache
from pathlib import Path


random.seed(7)

FONTS = ("standard", "slant", "small", "big", "mini", "banner", "shadow", "script")
WIDTHS = (10, 20, 40, 60, 80, 120)
JUSTIFICATIONS = ("auto", "left", "center", "right")
DIRECTIONS = ("auto", "left-to-right", "right-to-left")

NORMAL_WORDS = (
    "hello", "world", "figlet", "harbor", "agent", "render", "text", "golang",
    "beautiful", "quick", "brown", "fox", "jumps", "over", "lazy", "dog",
    "open", "source", "terminal", "display", "font", "banner", "welcome",
)
NOTES_RARE_TEXTS = (
    "AA", "_|", "|/", "/\\", "\\/", "[]", "{}", "()", "<>",
    "[ ] { } ( ) < >", "___", "|||", "\\\\", "hardblank",
)
SYMBOL_TEXTS = (
    "| / \\ _ [ ] { } ( ) < >",
    "double  spaces",
    "one   two    three",
    "é ß ñ",
    "café, jalapeño, Straße",
    "漢字 🙂 Ω Ж",
)
LONG_SENTENCES = (
    "A long sentence with several ordinary words should wrap across multiple lines "
    "when the selected width is narrow, while preserving its spaces and punctuation.",
    "FIGlet renders text with large character art; this deliberately long sentence "
    "continues far beyond the narrowest configured output width.",
)


class BinaryCapture:
    """Stand in for TextIOWrapper after pyfiglet.main detaches stdout."""

    def __init__(self):
        self.chunks = []

    def detach(self):
        return self

    def write(self, data):
        self.chunks.append(bytes(data))
        return len(data)

    def flush(self):
        pass

    def getvalue(self):
        return b"".join(self.chunks)


def locate_source():
    task_dir = Path(__file__).resolve().parents[1]
    candidates = (task_dir.parent / "pyfiglet", task_dir / "pyfiglet", task_dir)
    for candidate in candidates:
        if (candidate / "pyfiglet" / "__init__.py").is_file():
            return task_dir, candidate
    raise FileNotFoundError(
        "Could not find the pyfiglet source checkout beside the task folder"
    )


TASK_DIR, SOURCE_DIR = locate_source()
sys.path.insert(0, str(SOURCE_DIR))
from pyfiglet import CharNotPrinted, FigletFont, main as original_main  # noqa: E402


@lru_cache(maxsize=None)
def font_data(name):
    return FigletFont(name)


def text_fits_width(font_name, width, text):
    font = font_data(font_name)
    return all(
        ord(char) not in font.width or font.width[ord(char)] < width
        for char in text
    )


def render(args):
    old_argv = sys.argv
    old_stdout = sys.stdout
    captured = BinaryCapture()
    try:
        sys.argv = ["pyfiglet", *args]
        sys.stdout = captured
        status = original_main()
        if status not in (None, 0):
            raise RuntimeError(f"pyfiglet.main returned status {status} for {args!r}")
    finally:
        sys.argv = old_argv
        sys.stdout = old_stdout
    return captured.getvalue().decode("utf-8")


def make_text():
    kind = random.randrange(5)
    if kind == 0:
        return " ".join(random.choices(NORMAL_WORDS, k=random.randint(1, 5)))
    if kind == 1:
        return random.choice(NOTES_RARE_TEXTS)
    if kind == 2:
        return random.choice(SYMBOL_TEXTS)
    if kind == 3:
        return random.choice(LONG_SENTENCES)
    return " ".join(
        (random.choice(NORMAL_WORDS), random.choice(SYMBOL_TEXTS),
         random.choice(NORMAL_WORDS))
    )


def build_cases(count, already_used):
    # Balance each transform at exactly one case in four, independently.
    transform_flags = {}
    for flag in ("-r", "-F", "-s", "-n"):
        values = [True] * (count // 4) + [False] * (count - count // 4)
        random.shuffle(values)
        transform_flags[flag] = values

    cases = []
    used_here = set()
    for index in range(count):
        while True:
            font_name = random.choice(FONTS)
            width = random.choice(WIDTHS)
            text = make_text()
            # Width equal to a glyph can make the original builder repeatedly
            # wrap that glyph without advancing. Avoid such degenerate inputs.
            if not text_fits_width(font_name, width, text):
                continue
            args = [
                "-f", font_name,
                "-w", str(width),
                "-j", random.choice(JUSTIFICATIONS),
                "-D", random.choice(DIRECTIONS),
            ]
            for flag in ("-r", "-F", "-s", "-n"):
                if transform_flags[flag][index]:
                    args.append(flag)
            args.extend(("--", text))
            key = tuple(args)
            if key in already_used or key in used_here:
                continue
            try:
                output = render(args)
            except CharNotPrinted:
                # Some font glyphs are wider than the selected terminal width.
                continue
            used_here.add(key)
            break

        cases.append({"args": args, "out": output})
        if len(cases) % 25 == 0:
            print(f"Rendered {len(cases)} of {count} cases", file=sys.stderr)

    already_used.update(used_here)
    return cases


def write_jsonl(path, cases):
    path.parent.mkdir(parents=True, exist_ok=True)
    content = "".join(
        json.dumps(case, ensure_ascii=False, separators=(",", ":")) + "\n"
        for case in cases
    )
    path.write_bytes(content.encode("utf-8"))


def main():
    data_dir = TASK_DIR / "tests" / "data"
    used = set()
    visible = build_cases(2000, used)
    hidden = build_cases(2000, used)
    write_jsonl(data_dir / "visible.jsonl", visible)
    write_jsonl(data_dir / "hidden.jsonl", hidden)


if __name__ == "__main__":
    main()
