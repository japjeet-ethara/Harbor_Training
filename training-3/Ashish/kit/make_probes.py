"""Build the probe set that checks the parts of the port the exam cannot reach.

Usage: python make_probes.py <case_table.txt> <out.txt>

The 100,000-line exam is the thing that scores the task, but it cannot cover
everything the port has to get right. make_pool.py draws from fixed word banks,
so it contains no Greek capital sigma, no long s, no control-character
whitespace and only a handful of the 157 code points where Go's and CPython's
case mappings disagree.

This writes a separate set of inputs that targets exactly those gaps:

  * every code point from the generated case table, in ten word positions
    (alone, mid-word, first word, all-caps line, hyphenated, after Mc,
    inside an apostrophe name, underscore-prefixed, slashed, line-final)
  * Greek sigma in the contexts that trigger the Final_Sigma rule
  * the long s against the small-word list and the all-consonant rule
  * U+001C..U+001F and friends as word separators

Compare the port's output against the original the same way as the exam:

    uv run --no-project --python 3.14 python -I make_probes.py \
        key/case_table.txt probe_inputs.txt
    # run python titlecase (WITHOUT regex) over probe_inputs.txt -> probe_want.txt
    # run the Go port over probe_inputs.txt                      -> probe_got.txt
    diff probe_want.txt probe_got.txt

These inputs are deliberately NOT added to the exam. The exam's job is to
score; this file's job is to stop me tuning the port to the exam.
"""
import sys


def main():
    table_path, out_path = sys.argv[1], sys.argv[2]

    code_points = []
    for line in open(table_path, encoding="utf-8"):
        line = line.strip()
        if line.startswith("0x"):
            code_points.append(int(line.split(":")[0], 16))

    out = []

    def add(s):
        if "\n" not in s and "\r" not in s:
            out.append(s)

    for cp in code_points:
        c = chr(cp)
        add(c)
        add(c + "ord")
        add("the " + c + "ord of the thing")
        add((c + "ord of the thing").upper())
        add("x-" + c + "ord")
        add("mc" + c + "ord")
        add("o'" + c + "eilly's")
        add("_" + c + "ord")
        add(c + "ord/other")
        add("end with " + c)

    # Final_Sigma: a capital sigma lowercases to the final form at a word end.
    for s in ["\u039f\u0394\u039f\u03a3", "\u039f\u0394\u039f\u03a3 \u039a\u0391\u0399",
              "\u03a3\u039f\u03a6\u039f\u03a3", "\u039f\u03a3-\u039f\u03a3",
              "\u039f\u0394\u039f\u03a3.", "\u03a3", "\u0391\u03a3\u0391",
              "\u039f\u0394\u039f\u03a3' \u03a4\u0399",
              "\u03bf\u03b4\u03bf\u03c3", "\u039f\u0394\u039f\u03a3\u0301",
              "\u03a4\u039f \u039f\u0394\u039f\u03a3 \u039a\u0391\u0399 \u039f\u0394\u039f\u03a3"]:
        add(s)
        add(s.lower())
        add(s.title())

    # Long s (U+017F) folds to 's' under re.IGNORECASE, so it can match the
    # 's' in "as" and "vs" and can count towards the all-consonant rule.
    for s in ["a\u017f", "v\u017f", "v\u017f.", "a\u017f road", "road a\u017f",
              "\u017ft", "\u017ftx", "m\u017f", "m\u017f road", "nth \u017f",
              "b\u017fd", "a a\u017f b"]:
        add(s)
        add(s.upper())

    # Python counts these as whitespace, Go's unicode.IsSpace does not.
    for sep in ["\x1c", "\x1d", "\x1e", "\x1f", "\x85", "\u2028", "\u2029",
                "\v", "\f"]:
        add("the" + sep + "lord of the rings")
        add("a" + sep + "of")

    seen, uniq = set(), []
    for s in out:
        if s not in seen:
            seen.add(s)
            uniq.append(s)

    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.writelines(s + "\n" for s in uniq)
    print("wrote %d unique probe inputs to %s" % (len(uniq), out_path))


if __name__ == "__main__":
    main()