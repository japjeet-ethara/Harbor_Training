import functools
import io
import json
import pathlib
import random
import sys

REPO_DIR = pathlib.Path(__file__).resolve().parent.parent.parent / "pyfiglet"
sys.path.insert(0, str(REPO_DIR))

import pyfiglet

pyfiglet.FigletFont.preloadFont = classmethod(functools.lru_cache(maxsize=None)(pyfiglet.FigletFont.preloadFont.__func__))

FONTS = ["standard", "slant", "small", "big", "mini", "banner", "shadow", "script"]
WIDTHS = [10, 20, 40, 60, 80, 120]
JUSTIFIES = ["auto", "left", "center", "right"]
DIRECTIONS = ["auto", "left-to-right", "right-to-left"]

TEXTS = [
    "hello",
    "Hello World",
    "FIGlet 2026",
    "|| // \\\\ __",
    "|_| /\\ \\/ ><",
    "[] ][ {} }{ () )(",
    "| / \\ _ [ ] { } ( ) < >",
    "double  spaces   here",
    "The quick brown fox jumps over the lazy dog.",
    "smushing test: |< [()] >_< /\\/\\",
    "café résumé naïve über straße niño",
    "missing glyphs: ~ ` ^ ÿ \x7f",
    "A",
    "1234567890",
    "leading and trailing",
    "line1\nline2",
    "right-to-left |_| test",
    "Big X >< /\\ \\/ test",
]

def run_original(args):
    old_argv = sys.argv
    old_stdout = sys.stdout
    raw_buf = io.BytesIO()
    wrapper = io.TextIOWrapper(raw_buf, encoding="utf-8", newline="\n")
    try:
        sys.argv = ["pyfiglet"] + args
        sys.stdout = wrapper
        pyfiglet.main()
        if sys.stdout is wrapper:
            sys.stdout.flush()
    finally:
        sys.argv = old_argv
        sys.stdout = old_stdout
    return raw_buf.getvalue().decode("utf-8")

def generate_dataset(rng, count, label, seen):
    cases = []
    while len(cases) < count:
        args = []
        font = rng.choice(FONTS) if rng.random() < 0.85 else "standard"
        if font != "standard" or rng.random() < 0.5:
            args.extend(["-f", font])
        if rng.random() < 0.85:
            w = rng.choice(WIDTHS)
            if w == 10 and font in ("big", "banner", "shadow", "script", "slant", "standard"):
                w = rng.choice([20, 40, 60, 80, 120])
            args.extend(["-w", str(w)])
        if rng.random() < 0.80:
            args.extend(["-j", rng.choice(JUSTIFIES)])
        if rng.random() < 0.80:
            args.extend(["-D", rng.choice(DIRECTIONS)])
        if rng.random() < 0.25:
            args.append("-r")
        if rng.random() < 0.25:
            args.append("-F")
        if rng.random() < 0.25:
            args.append("-s")
        if rng.random() < 0.25:
            args.append("-n")

        if rng.random() < 0.7:
            text_parts = [rng.choice(TEXTS)]
        else:
            text_parts = [rng.choice(["hello", "world", "|_|", "><", "test", "foo", "bar"]) for _ in range(rng.randint(2, 4))]

        full_args = args + text_parts
        key = tuple(full_args)
        if key in seen:
            continue
        seen.add(key)

        try:
            out = run_original(full_args)
        except (pyfiglet.CharNotPrinted, SystemExit):
            continue

        cases.append({"args": full_args, "out": out})
        if len(cases) % 250 == 0:
            print(f"[{label}] {len(cases)}/{count} done...", flush=True)
    return cases

def main():
    rng = random.Random(7)
    seen = set()
    visible = generate_dataset(rng, 2000, "visible", seen)
    hidden = generate_dataset(rng, 2000, "hidden", seen)

    out_dir = pathlib.Path(__file__).resolve().parent / "data"
    out_dir.mkdir(parents=True, exist_ok=True)

    vis_path = out_dir / "visible.jsonl"
    hid_path = out_dir / "hidden.jsonl"

    with vis_path.open("w", encoding="utf-8", newline="\n") as f:
        for row in visible:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    with hid_path.open("w", encoding="utf-8", newline="\n") as f:
        for row in hidden:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    rtl_count = sum(1 for c in hidden if "right-to-left" in c["args"])
    narrow_count = sum(1 for c in hidden if any(w in c["args"] for w in ["10", "20"]))
    print(f"Generated {len(visible)} visible and {len(hidden)} hidden cases.")
    print(f"Hidden stats -> right-to-left: {rtl_count}, narrow (<=24): {narrow_count}")

if __name__ == "__main__":
    main()
