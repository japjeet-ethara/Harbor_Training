"""Round-2 regression titles: every round-1 title (all required now) plus focused
cases for dotless i, long s, Python's extra whitespace and Unicode 16 word characters.

Usage: python -I -B make_regression_cases_r2.py <pool.txt> <labels.tsv>
Expected outputs are frozen separately with the trainer's answers.py.
"""
import importlib.util
import pathlib
import sys

spec = importlib.util.spec_from_file_location(
    "r1", pathlib.Path(__file__).with_name("make_regression_cases.py"))
r1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r1)

DOTLESS, LONG_S, KELVIN = "ı", "ſ", "K"
GARAY_SMALL_A = "\U00010d70"   # GARAY SMALL LETTER A (Unicode 16.0)
GARAY_DIGIT_ONE = "\U00010d41"  # GARAY DIGIT ONE (Unicode 16.0)
HIEROGLYPH = "\U00013460"       # Egyptian Hieroglyphs Extended-A (Unicode 16.0)

RENAMED = {
    "residual: re.I folding": None,  # split below by character
    "residual: \\s": "extra whitespace",
    "residual: \\w Unicode 16": "word chars (Unicode 16)",
}

NEW = [
    ("dotless i", "small word first, SMALL_FIRST capitalize()", f"{DOTLESS}n the night"),
    ("dotless i", "small word last, SMALL_LAST capitalize()", f"night {DOTLESS}f"),
    ("dotless i", "small word with dot", f"the v{DOTLESS}a. road"),
    ("dotless i", "hyphen parts", f"self-{DOTLESS}n-law"),
    ("dotless i", "slash parts", f"and/{DOTLESS}n"),
    ("dotless i", "all-caps test: upper() of ı is I", f"NIGHT {DOTLESS}N"),
    ("long s", "small word first", f"a{LONG_S} the night"),
    ("long s", "small word with dot", f"war v{LONG_S}. peace"),
    ("long s", "honorific", f"m{LONG_S} smith"),
    ("long s", "apostrophe tail ['s]{2}", f"o'neil'{LONG_S}"),
    ("long s", "CAPFIRST upper() (control)", f"the {LONG_S}how"),
    ("Kelvin sign", "consonant acronym", f"{KELVIN}rr"),
    ("Kelvin sign", "consonant acronym, all Kelvin", KELVIN * 3),
    ("extra whitespace", "U+001C/U+001D/U+001E split words", "the\x1cend\x1dof\x1eit"),
    ("extra whitespace", "U+001F before a small last word", "night\x1fof"),
    ("extra whitespace", "all-caps line", "NIGHT\x1eDAY"),
    ("extra whitespace", "leading U+001F", "\x1fthe night"),
    ("word chars (Unicode 16)", "\\b before a small last word", f"word {GARAY_SMALL_A}a"),
    ("word chars (Unicode 16)", "INLINE_PERIOD with a new letter", f"x.{HIEROGLYPH}"),
    ("word chars (Unicode 16)", "hyphen parts", f"{GARAY_SMALL_A}ord-{GARAY_SMALL_A}ord"),
    ("word chars (Unicode 16)", "new digit makes an ordinary word", f"{GARAY_DIGIT_ONE}st place"),
]


def main():
    pool, labels = sys.argv[1], sys.argv[2]
    rows = []
    for group, _req, note, title in r1.CASES:
        if group == "residual: re.I folding":
            group = "dotless i" if DOTLESS in title else "long s"
        else:
            group = RENAMED.get(group, group)
        rows.append((group, 1, note, title))
    rows += [(g, 1, n, t) for g, n, t in NEW]
    titles = [r[3] for r in rows]
    assert len(set(titles)) == len(titles), "duplicate titles"
    assert all("\n" not in t and "\r" not in t for t in titles)
    with open(pool, "w", encoding="utf-8", newline="\n") as f:
        f.writelines(t + "\n" for t in titles)
    with open(labels, "w", encoding="utf-8", newline="\n") as f:
        for i, (group, req, note, _) in enumerate(rows, 1):
            f.write(f"{i}\t{group}\t{req}\t{note}\n")
    print(f"cases {len(rows)} (round 1: {len(r1.CASES)}, new: {len(NEW)}), all required")


if __name__ == "__main__":
    main()
