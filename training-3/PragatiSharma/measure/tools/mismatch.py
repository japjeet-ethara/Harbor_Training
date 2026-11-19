"""Explain a port's mismatches against a frozen suite (analysis only).

Usage: python -I -B mismatch.py <suite_dir> <got.txt> <out.tsv> [families.py]
Prints a cause summary; writes every mismatch to out.tsv (line, cause, input, want, got as repr).
"""
import importlib.util
import re
import sys
from collections import Counter, defaultdict


def records(path):
    data = open(path, "rb").read()
    if data.endswith(b"\n"):
        data = data[:-1]
    return [r.decode("utf-8") for r in data.split(b"\n")] if data else []


def go_simple_upper(s):
    # Approximates Go's strings.ToUpper: one rune in, one rune out; characters whose
    # Python upper() has several code points have no simple mapping and stay unchanged.
    return "".join(u if len(u := c.upper()) == 1 else c for c in s)


def cause_of(word):
    lig = [c for c in word if 0xFB00 <= ord(c) <= 0xFB06]
    if lig:
        return "ligature " + "".join(sorted(set(lig)))
    if "İ" in word:
        return "dotted capital I (U+0130)"
    if "ß" in word:
        return "sharp s (U+00DF)"
    other = sorted({c for c in word if len(c.upper()) > 1 or len(c.lower()) > 1 or len(c.title()) > 1})
    if other:
        return "other case-expanding " + "".join(other)
    return "other"


def main():
    suite, got_path, out_tsv = sys.argv[1], sys.argv[2], sys.argv[3]
    fam = None
    if len(sys.argv) > 4:
        spec = importlib.util.spec_from_file_location("families", sys.argv[4])
        fam = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(fam)
    inputs, want, got = records(f"{suite}/inputs.txt"), records(f"{suite}/answers.txt"), records(got_path)
    assert len(inputs) == len(want) == len(got)
    bad = [i for i in range(len(want)) if want[i] != got[i]]

    line_causes = Counter()
    word_causes = Counter()
    word_examples = defaultdict(Counter)
    line_examples = defaultdict(list)
    allcaps_ctx = Counter()
    unaligned = 0
    with open(out_tsv, "w", encoding="utf-8", newline="\n") as tsv:
        tsv.write("line\tcause\tinput\twant\tgot\n")
        for i in bad:
            wi, ww, wg = (re.split(r"(\s)", s)[::2] for s in (inputs[i], want[i], got[i]))
            causes = set()
            if len(wi) == len(ww) == len(wg):
                py_caps = inputs[i].upper() == inputs[i]
                go_caps = go_simple_upper(inputs[i]) == inputs[i]
                for a, b, c in zip(wi, ww, wg):
                    if b != c:
                        k = cause_of(a)
                        causes.add(k)
                        word_causes[k] += 1
                        word_examples[k][(a, b, c)] += 1
                        allcaps_ctx[(k, py_caps, go_caps)] += 1
            else:
                unaligned += 1
                causes.add("word split differs")
            sig = " + ".join(sorted(causes))
            line_causes[sig] += 1
            if len(line_examples[sig]) < 3:
                line_examples[sig].append(i)
            tsv.write(f"{i + 1}\t{sig}\t{inputs[i]!r}\t{want[i]!r}\t{got[i]!r}\n")

    print(f"records {len(want)}  wrong {len(bad)}  (word-split mismatch lines: {unaligned})")
    print("\nlines by cause signature:")
    for k, v in line_causes.most_common():
        print(f"  {v:6d}  {k}")
    print("\ndiffering words by cause (Python all-caps line?, Go-simple all-caps line?):")
    for (k, pc, gc), v in sorted(allcaps_ctx.items(), key=lambda x: -x[1]):
        print(f"  {v:6d}  {k}  py_allcaps={pc} go_allcaps={gc}")
    print("\nmost frequent differing words per cause (input -> want | got):")
    for k, _ in word_causes.most_common():
        print(f"  [{k}]")
        for (a, b, c), v in word_examples[k].most_common(6):
            print(f"    {v:5d}x  {a!r} -> want {b!r} | got {c!r}")
    print("\nrepresentative full lines:")
    for k, idx in line_examples.items():
        print(f"  [{k}]")
        for i in idx:
            print(f"    line {i + 1}\n      input {inputs[i]!r}\n      want  {want[i]!r}\n      got   {got[i]!r}")
    if fam:
        tot, wrong = Counter(), Counter()
        badset = set(bad)
        for i, t in enumerate(inputs):
            for f in fam.families(t):
                tot[f] += 1
                if i in badset:
                    wrong[f] += 1
        print("\nfamilies (titles in suite / titles wrong):")
        for f in fam.ORDER:
            if tot[f]:
                print(f"  {f:40} {tot[f]:7d} {wrong[f]:6d}")


if __name__ == "__main__":
    main()
