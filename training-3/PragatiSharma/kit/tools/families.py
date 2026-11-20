"""Count titlecase word families in title files (inspection only; writes nothing).

Usage:
  python -I families.py <label>=<titles.txt> ... [--sample <label>=<make_pool.py>:<count>:<seed>]

Families follow the branches and character classes of the original
titlecase() in standard-library `re` mode. A title counts once per family.
"""
import importlib.util
import random
import re
import sys
import unicodedata

PUNCT = set("""!"“#$%&'‘()*+,-–‒—―./:;?@[\\]_`{|}~""")
SMALL = r"a|an|and|as|at|but|by|en|for|if|in|of|on|or|the|to|v\.?|via|vs\.?"
SMALL_WORDS = re.compile(r"^(%s)$" % SMALL, re.I)
SUBPHRASE = re.compile(r"([:.;?!\-–‒—―][ ])(%s)" % SMALL)
MAC_MC = re.compile(r"^([Mm]c|MC)(\w.+)")
MR_MRS_MS_DR = re.compile(r"^((m((rs?)|s))|Dr)$", re.I)
INLINE_PERIOD = re.compile(r"[\w][.][\w]", re.I)
UC_ELSEWHERE = re.compile(r"[%s]*?[a-zA-Z]+[A-Z]+?" % re.escape("".join(sorted(PUNCT))))
APOS_SECOND = re.compile(r"^[dol]['‘][\w]+(?:['s]{2})?$", re.I)
UC_INITIALS = re.compile(r"^(?:[A-Z]\.|[A-Z]\.[A-Z])+$")
CONSONANTS = re.compile(r"\A[bcdfghjklmnpqrstvwxz]+\Z", re.I)
ORDINAL = re.compile(r"^\d+(st|nd|rd|th)$", re.I)
COMMON_SPACES = {" ", "\t", " ", " ", " ", " "}
ZERO_WIDTH = {"​", "‌", "‍", "﻿"}


def words(line):
    return re.split(r"(\s)", line)[::2]


def families(line):
    ws = [w for w in words(line) if w]
    caps = line.upper() == line
    f = set()
    if any(SMALL_WORDS.match(w) for w in ws): f.add("small word")
    if SUBPHRASE.search(line): f.add("sub-phrase break + small word")
    if caps and any(c.isalpha() for c in line): f.add("all-caps line")
    if any(UC_INITIALS.match(w) for w in ws): f.add("initials (A.B.)")
    if any(APOS_SECOND.match(w) for w in ws): f.add("d'/l'/o' apostrophe")
    if any(MAC_MC.match(w) for w in ws): f.add("Mc prefix")
    if any(MR_MRS_MS_DR.match(w) for w in ws): f.add("honorific (exact)")
    if any(re.match(r"^(mr|mrs|ms|dr)[.,]$", w, re.I) for w in ws): f.add("honorific + punctuation")
    if any(INLINE_PERIOD.search(w) for w in ws): f.add("inline period (domain, v1.2)")
    if not caps and any(UC_ELSEWHERE.match(w) for w in ws): f.add("ASCII internal caps")
    if any("/" in w and "//" not in w for w in ws): f.add("slash split")
    if any("//" in w for w in ws): f.add("double slash (URL)")
    if any("//" in w and "-" in w and not INLINE_PERIOD.search(w) for w in ws): f.add("URL/path with hyphen, no period")
    if any("-" in w for w in ws): f.add("hyphen split")
    if any(CONSONANTS.search(w) and len(w) > 2 for w in ws): f.add("consonant acronym")
    if any(ORDINAL.match(w) for w in ws): f.add("ordinal (21st)")
    if any(any(c.isdigit() for c in w) and any(c.isalpha() for c in w) and not ORDINAL.match(w) for w in ws):
        f.add("other letter+digit word (mp3, 4k)")
    if re.search(r"\d\.\d", line): f.add("decimal number")
    if not any(c.isalpha() for c in line): f.add("no-letter title")
    if any(c.isalpha() and ord(c) > 127 for c in line): f.add("non-ASCII letters")
    if any(len(c.upper()) > 1 or len(c.lower()) > 1 for c in line): f.add("case-expanding char (ß, ﬁ, İ)")
    if any(any(ord(c) > 127 and c.isalpha() for c in w) and any(c.isupper() for c in w[1:]) and not w.isupper() for w in ws):
        f.add("non-ASCII internal caps")
    if "’" in line: f.add("typographic apostrophe ’")
    if any(re.search(r"\w['’]\w", w) and not APOS_SECOND.match(w) for w in ws): f.add("contraction/possessive")
    if any(unicodedata.category(c)[0] in "PS" and c not in PUNCT for c in line): f.add("punctuation/symbol outside PUNCT")
    if any(ord(c) > 0xFFFF for c in line): f.add("emoji / non-BMP")
    if "\t" in line or " " in line: f.add("tab or NBSP")
    if any(c.isspace() and c not in COMMON_SPACES for c in line): f.add("other Unicode space")
    if any(c in ZERO_WIDTH for c in line): f.add("zero-width char")
    return f


ORDER = [
    "small word", "sub-phrase break + small word", "all-caps line", "initials (A.B.)",
    "d'/l'/o' apostrophe", "Mc prefix", "honorific (exact)", "inline period (domain, v1.2)",
    "ASCII internal caps", "slash split", "double slash (URL)", "hyphen split",
    "consonant acronym", "ordinal (21st)", "tab or NBSP",
    "honorific + punctuation", "other letter+digit word (mp3, 4k)", "decimal number",
    "no-letter title", "non-ASCII letters", "case-expanding char (ß, ﬁ, İ)",
    "non-ASCII internal caps", "typographic apostrophe ’", "contraction/possessive",
    "punctuation/symbol outside PUNCT", "emoji / non-BMP", "other Unicode space",
    "zero-width char", "URL/path with hyphen, no period",
]


def read_titles(path):
    data = open(path, "rb").read().decode("utf-8")
    return data[:-1].split("\n") if data else []


def sample(spec):
    path, count, seed = spec.rsplit(":", 2)
    spec_obj = importlib.util.spec_from_file_location("make_pool_sample", path)
    mod = importlib.util.module_from_spec(spec_obj)
    spec_obj.loader.exec_module(mod)
    rng, seen, out = random.Random(int(seed)), set(), []
    while len(out) < int(count):
        t = mod.line(rng)
        if t in seen or "\n" in t or "\r" in t:
            continue
        seen.add(t)
        out.append(t)
    return out


def main():
    columns = []
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--sample":
            label, spec = args[i + 1].split("=", 1)
            columns.append((label, sample(spec)))
            i += 2
        else:
            label, path = args[i].split("=", 1)
            columns.append((label, read_titles(path)))
            i += 1
    counts = []
    for _, titles in columns:
        c = {}
        for t in titles:
            for fam in families(t):
                c[fam] = c.get(fam, 0) + 1
        counts.append(c)
    head = f"{'family':40}" + "".join(f"{label:>18}" for label, _ in columns)
    print(head)
    print(f"{'(titles)':40}" + "".join(f"{len(t):>18,}" for _, t in columns))
    for fam in ORDER:
        print(f"{fam:40}" + "".join(f"{c.get(fam, 0):>18,}" for c in counts))


if __name__ == "__main__":
    main()
