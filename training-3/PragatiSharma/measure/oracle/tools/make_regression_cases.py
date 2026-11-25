"""Write the focused regression titles (inputs only; answers come from the reference).

Usage: python -I -B make_regression_cases.py <pool.txt> <labels.tsv>
labels.tsv rows: line, group, required (1/0), note.
Expected outputs are frozen separately with the trainer's answers.py.
"""
import sys

I_DOT = "İ"  # İ LATIN CAPITAL LETTER I WITH DOT ABOVE
FI, FL, FFI, ST = "ﬁ", "ﬂ", "ﬃ", "ﬆ"

CASES = [
    # group, required, note, title
    ("ligature", 1, "ligature starts the word", f"{FI}nal"),
    ("ligature", 1, "ligature starts the word", f"{FL}ight"),
    ("ligature", 1, "three-letter ligature", f"{FFI}ce"),
    ("ligature", 1, "ligature st", f"{ST}op"),
    ("ligature", 1, "ligature not first (control)", f"o{FFI}ce"),
    ("ligature", 1, "leading punctuation", f'"{FI}nal"'),
    ("ligature", 1, "two ligature words", f"{FI}nal {FL}ight"),
    ("ligature", 1, "small words around", f"the {FI}nal of the night"),
    ("ligature", 1, "ligature alone", f"{FI}"),
    ("ligature all-caps", 1, "ligature stops the line being all-caps", f"MACHINE {FI}"),
    ("ligature all-caps", 1, "ligature stops the line being all-caps", f"NASA {FL} TEAM"),
    ("ligature hyphen", 1, "hyphen part", f"self-{FI}nal"),
    ("ligature hyphen", 1, "both hyphen parts", f"{FI}nal-{FL}ight"),
    ("ligature slash", 1, "both slash parts", f"{FI}nal/{FL}ight"),
    ("ligature slash", 1, "small word and ligature", f"and/{FI}nal"),
    ("ligature apostrophe", 1, "APOS_SECOND upper of third character", f"d'{FI}nal"),
    ("ligature apostrophe", 1, "APOS_SECOND upper of third character", f"o'{FL}ight"),
    ("dotted I", 1, "all-caps line", f"{I_DOT}ZMIR"),
    ("dotted I", 1, "all-caps line", f"{I_DOT}STANBUL NIGHT"),
    ("dotted I", 1, "all-caps line, small word first", f"THE {I_DOT}STANBUL STORY"),
    ("dotted I", 1, "all-caps line, alone", f"{I_DOT}"),
    ("dotted I", 1, "all-caps line, doubled", f"{I_DOT}{I_DOT}"),
    ("dotted I", 1, "mixed-case line (control)", f"{I_DOT}zmir"),
    ("dotted I", 1, "mixed-case line (control)", f"{I_DOT}STANBUL night"),
    ("dotted I hyphen", 1, "all-caps line", f"STEP-{I_DOT}STANBUL"),
    ("dotted I hyphen", 1, "all-caps line", f"{I_DOT}STANBUL-{I_DOT}ZMIR"),
    ("dotted I hyphen", 1, "mixed line, all-caps hyphen parts", f"night {I_DOT}STANBUL-{I_DOT}ZMIR"),
    ("dotted I hyphen", 1, "mixed line, leading hyphen", f"trip to -{I_DOT}STANBUL"),
    ("dotted I slash", 1, "all-caps line", f"{I_DOT}STANBUL/{I_DOT}ZMIR"),
    ("dotted I slash", 1, "mixed line, all-caps slash part", f"a/{I_DOT}STANBUL"),
    ("dotted I slash", 1, "mixed line, all-caps slash parts", f"tour {I_DOT}ZMIR/{I_DOT}STANBUL"),
    ("dotted I other rules", 1, "Mc prefix, recursive call", f"MC{I_DOT}ZMIR"),
    ("dotted I other rules", 1, "apostrophe rule (no lowering)", f"D'{I_DOT}ZMIR"),
    ("dotted I other rules", 1, "small word via re.I, then lower()", f"{I_DOT}N THE NIGHT"),
    ("dotted I other rules", 1, "small word last, lower()", f"night {I_DOT}n"),
    ("dotted I other rules", 1, "SMALL_LAST capitalize() lowers the rest", f"the v{I_DOT}a."),
    ("other full mappings", 1, "sharp s, mixed case", "straße"),
    ("other full mappings", 1, "sharp s stops the line being all-caps", "STRAßE"),
    ("other full mappings", 1, "capital sharp s, all-caps line", "STRAẞE"),
    ("other full mappings", 1, "n preceded by apostrophe", "ŉ"),
    ("other full mappings", 1, "Armenian ligature", "և"),
    ("other full mappings", 1, "final sigma, all-caps line", "ΟΔΟΣ"),
    ("other full mappings", 1, "final and initial sigma", "ΟΔΟΣ ΣΟΦΙΑ"),
    ("other full mappings", 1, "final sigma before punctuation", "ΟΔΟΣ."),
    ("other full mappings", 1, "final sigma in hyphen parts", "ΟΔΟΣ-ΟΔΟΣ"),
    ("other full mappings", 1, "digraph, CAPFIRST", "ǆungla"),
    ("control", 1, "plain title", "the lord of the rings"),
    ("control", 1, "Mc prefix", "MCDONALD"),
    ("control", 1, "hyphens and small words", "step-by-step guide to the city"),
    # Not upper()/lower(): known remaining differences, reported only.
    ("residual: re.I folding", 0, "dotless i matches i under re.IGNORECASE", "the ın crowd"),
    ("residual: re.I folding", 0, "long s matches s under re.IGNORECASE", "ſtr"),
    ("residual: \\s", 0, "U+001F is \\s in Python, not in Go unicode.IsSpace", "word\x1fword"),
    ("residual: \\w Unicode 16", 0, "Garay letter (Unicode 16.0) is \\w in Python 3.14", "\U00010d70ord"),
]


def main():
    pool, labels = sys.argv[1], sys.argv[2]
    titles = [c[3] for c in CASES]
    assert len(set(titles)) == len(titles), "duplicate titles"
    assert all("\n" not in t and "\r" not in t for t in titles)
    with open(pool, "w", encoding="utf-8", newline="\n") as f:
        f.writelines(t + "\n" for t in titles)
    with open(labels, "w", encoding="utf-8", newline="\n") as f:
        for i, (group, req, note, _) in enumerate(CASES, 1):
            f.write(f"{i}\t{group}\t{req}\t{note}\n")
    print(f"cases {len(CASES)} (required {sum(c[1] for c in CASES)}, residual {sum(1 - c[1] for c in CASES)})")


if __name__ == "__main__":
    main()
