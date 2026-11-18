# NOTES — python-titlecase (Step 1)

- Repo: https://github.com/ppannuto/python-titlecase
- Commit SHA: `42f43e2de55bf003b286c6f8e8d8b2d26676a167`
- Commit date: `2024-04-05T22:03:59-07:00`
- Version in source: `2.4.1`
- Licence: **MIT** (`LICENSE.txt`, Copyright (c) 2021 Patrick William Pannuto). OK to use.

## Reference behaviour

`titlecase/__init__.py` tries `import regex` first and falls back to stdlib `re`.
The two branches use **different** regexes for INLINE_PERIOD, UC_ELSEWHERE,
CAPFIRST, APOS_SECOND and UC_INITIALS. This task freezes the **stdlib `re`
fallback**: `tests/gen.py` blocks `regex` before importing, so answers do not
depend on what is installed on the author's machine. The instruction says this
explicitly, because an agent cannot know which branch is meant otherwise.

Reference call: `titlecase(line)` with all defaults (no callback,
`small_first_last=True`, no blank-line preservation, no space normalisation).

## Rules applied by `titlecase()` (in order), each with a checked example

All examples below were produced by running the original code
(`python3 -c "import sys; sys.modules['regex']=None; from titlecase import titlecase; print(titlecase('...'))"`).

Per line: `all_caps = line.upper() == line`. The line is split on single
whitespace characters (`re.split(r'(\s)')`), so runs of spaces are kept exactly.
Each word then goes through the first rule that applies:

| # | Rule | Input | Output |
|---|------|-------|--------|
| 1 | **Initials in an all-caps line** (`^(?:[A-Z]\.\|[A-Z]\.[A-Z])+$`) are kept | `U.S.A. IS BIG` | `U.S.A. Is Big` |
| 2 | **Apostrophe second** (`d'`, `o'`, `l'` + `'` or `‘`): d/l lower-cased, o upper-cased, letter after the apostrophe upper-cased, rest untouched | `d'artagnan returns` | `d'Artagnan Returns` |
|   |   | `o'neil was here` | `O'Neil Was Here` |
|   |   | `D'ARTAGNAN` | `d'ARTAGNAN` |
|   |   | `o‘neil` (left quote) vs `o’neil` (right quote) | `O‘Neil` vs `O’neil` |
| 3 | **Mc / MC prefix**: `Mc` + titlecase(rest) (recursive, with small-first/last) | `mcdonald's menu` | `McDonald's Menu` |
|   |   | `MCDONALD` | `McDonald` |
| 4 | **Mr / Mrs / Ms / Dr** (whole word, any case): first letter upper | `mr smith and dr jones` | `Mr Smith and Dr Jones` |
| 5 | **Inline period** (`\w.\w` anywhere) → word kept as is | `node.js is fun` | `node.js Is Fun` |
|   |   | `visit http://example.com today` | `Visit http://example.com Today` |
| 6 | **Uppercase elsewhere** (not in an all-caps line): leading punctuation, then an ASCII-letter run with an uppercase letter after its first letter → kept | `the iPhone and eBay` | `The iPhone and eBay` |
| 7 | **Small words** (`a an and as at but by en for if in of on or the to v v. via vs vs.`) → lower-case | `the lord of the rings` | `The Lord of the Rings` |
| 8 | **Slash** (contains `/` but not `//`): each part titlecased (no small-first/last) | `and/or input/output` | `And/or Input/Output` |
|   |   | `w/o sugar` | `W/O Sugar` |
| 9 | **Hyphen**: each part titlecased (no small-first/last); each part gets its own all-caps test | `step-by-step guide` | `Step-by-Step Guide` |
| 10 | All-caps line → word lower-cased before the next two rules | `NASA LAUNCHES ROCKET` | `Nasa Launches Rocket` |
| 11 | **All consonants, length > 2** (`bcdfghjklmnpqrstvwxz`, *y counts as a vowel*) → upper-case | `xml and html in css` | `XML and HTML in CSS` |
|    |   | `nyc bbc pdf` | `Nyc BBC PDF` |
|    |   | `st louis` (length 2) | `St Louis` |
| 12 | **Capitalise first**: skip leading punctuation, upper-case the first word character. `_` is both punctuation *and* a word character, so a leading `_` blocks it | `_private member` | `_private Member` |
| 13 | **Small first word** (after leading punctuation, followed by a word boundary) → capitalised | `“the” quote` | `“The” Quote` |
| 14 | **Small last word** (optionally followed by one punctuation char) → capitalised | `the end of` | `The End Of` |
| 15 | **Sub-phrase**: after `: . ; ? ! - – ‒ — ―` + a single space, a lower-case small word gets a capital (case-sensitive, no word-boundary check, runs on the joined line) | `what is this? a test` | `What Is This? A Test` |
|    |   | `THE U.S.A. AND F.B.I.` | `The U.S.A. And F.B.I.` |
|    |   | `foo: aBc` | `Foo: ABc` |

Note on row 10: `NASA launches rocket` → `NASA Launches Rocket` because the line is not
all caps, so `NASA` hits rule 6 (uppercase elsewhere) and is kept.

## Examples where a quick reading of the code gives the WRONG answer (keep — these are the rare cases)

These are the places where I (acting as the worker agent) first predicted wrongly,
then corrected after running the original:

1. `nyc` → `Nyc`, not `NYC` — `y` is removed from the consonant set.
2. `THE U.S.A. AND F.B.I.` → `And` is capitalised — SUBPHRASE runs after the
   small-word rule, and `.` + space counts as a sub-phrase start.
3. `foo: aBc` → `ABc` — SUBPHRASE has **no** `\b`, so it hits the `a` of any word.
4. `it’s o’neil` → `O’neil` — only `'` and `‘` (left quote) count for rule 2; `’` does not.
5. `_private` → `_private` — `_` is in PUNCT *and* `\w`; the lazy CAPFIRST match stops on it.
6. `a v. b` → `A v. B` — `v.` is a small word, kept lower even mid-line.
7. `this is v. that` → `v.` stays lower, but `vs.` alone → `Vs.` (small-last).
8. `D'ARTAGNAN` → `d'ARTAGNAN` — rule 2 fires before the all-caps lower-casing.
9. `3d printing` → `3d` — CAPFIRST upper-cases the first word char, which is the digit.
10. Hyphen parts get their **own** all-caps test: `foo-BAR baz` → `Foo-Bar Baz` (the part
    `BAR` is all caps on its own, so it is lower-cased then capitalised).
    I first guessed `FOO-bar` → `Foo-Bar`; wrong — it stays `FOO-bar`, because rule 6
    (uppercase elsewhere) sees `FOO` and keeps the whole word before the hyphen rule runs.
11. `NASA LAUNCHES ROCKET` → `Nasa Launches Rocket` — in an all-caps line rule 6 is
    off, so `NASA` is lower-cased and capitalised. I first guessed it stays `NASA`.
