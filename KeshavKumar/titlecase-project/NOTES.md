# NOTES — python-titlecase

## Source

| Field   | Value |
|---------|-------|
| Repo    | https://github.com/ppannuto/python-titlecase |
| Commit  | `42f43e2de55bf003b286c6f8e8d8b2d26676a167` |
| Date    | `2024-04-05T22:03:59-07:00` |
| Version | `2.4.1` (`__version__` in `titlecase/__init__.py`) |
| Licence | **MIT** (`LICENSE.txt`, Copyright (c) 2021 Patrick William Pannuto) |

**Important:** the code uses the third-party `regex` module if it is installed and
falls back to Python's built-in `re` if it isn't. On this machine `regex` is **not**
installed (`REGEX_AVAILABLE = False`). All examples below, and the expected answers,
come from the **`re` fallback**. Keep it that way, or the answers will change.

## What the function does

`titlecase(text)` turns text into Title Case, following the New York Times style
rules (Perl original by John Gruber, ported to Python). It is cleverer than
`str.title()`: it keeps small words lowercase and leaves acronyms, URLs and
mixed-case words alone. It also handles names such as McDonald and O'Neil.

## Rules (in the order the code applies them)

All outputs were produced by running the original code (default arguments).

| # | Rule | Input | Output |
|---|------|-------|--------|
| 1 | **Lines.** Text is split on runs of `\r`/`\n`. Blank lines are dropped and lines are re-joined with `\n`. | `"first line\nsecond line\n\nthird"` | `"First Line\nSecond Line\nThird"` |
| 2 | **Words.** Each line is split on single whitespace characters (`\s`, including tabs and NBSP). The original whitespace is put back unchanged. | `"hello   big\tworld"` | `"Hello   Big\tWorld"` |
| 3 | **All-caps line detection.** If `line.upper() == line`, the whole line counts as "all caps": words are lowercased first and then capitalized. | `"THE GREAT GATSBY"` | `"The Great Gatsby"` |
| 4 | **Uppercase initials (all-caps lines only).** Words such as `U.S.` (`^(?:[A-Z]\.\|[A-Z]\.[A-Z])+$`) are kept as they are. | `"THE U.S. ARMY"` | `"The U.S. Army"` |
| 5 | **d' / o' / l' prefix (APOS_SECOND).** The letter after the apostrophe is uppercased. A consonant prefix (`d`, `l`) becomes lowercase and a vowel prefix (`o`) becomes uppercase. | `"o'neil and d'artagnan"` | `"O'Neil and d'Artagnan"` |
| 6 | **Mc / MC prefix (MAC_MC).** `Mc` is kept and the **rest of the word is titlecased again, recursively**. `Mac` is *not* handled. | `"old mcdonald had a farm"` | `"Old McDonald Had a Farm"` |
| 7 | **Mr / Mrs / Ms / Dr.** Only the first letter is uppercased. The rest is left as it is. | `"mr smith and dr jones"` | `"Mr Smith and Dr Jones"` |
| 8 | **Inline period.** A word containing letter`.`letter (domains, `e.g.`) is kept exactly as written. | `"visit example.com today"` | `"Visit example.com Today"` |
| 9 | **Uppercase elsewhere (mixed-case lines only).** A word with a capital letter after its first letter is kept exactly as written. | `"my new iPhone"` / `"the NASA mission"` | `"My New iPhone"` / `"The NASA Mission"` |
| 10 | **Small words → lowercase.** `a an and as at but by en for if in of on or the to v v. via vs vs.` (case-insensitive). | `"war and peace"` | `"War and Peace"` |
| 11 | **Slash.** A word containing `/` (but not `//`) is split on `/`, each part is titlecased with first/last rules off, then re-joined. | `"this/that"` | `"This/That"` |
| 12 | **Hyphen.** A word containing `-` is split on `-`, each part is titlecased with first/last rules off, then re-joined. | `"step-by-step guide"` | `"Step-by-Step Guide"` |
| 13 | **All consonants → ACRONYM.** A word of 3+ letters with no `a e i o u y` is uppercased. Words of 2 letters or fewer are not. | `"the bbc and cnn"` / `"st louis"` | `"The BBC and CNN"` / `"St Louis"` |
| 14 | **Normal word.** The first letter after any leading punctuation is uppercased. The rest is left as it is. | `'"hello" (world)'` | `'"Hello" (World)'` |
| 15 | **First word small → capitalized.** Applies even after leading punctuation. | `"the lord of the rings"` | `"The Lord of the Rings"` |
| 16 | **Last word small → capitalized.** One trailing punctuation mark is allowed. | `"what is it for?"` | `"What Is It For?"` |
| 17 | **Sub-phrase.** A small word right after `: . ; ? ! - – ‒ — ―` plus a space is capitalized. | `"star wars: a new hope"` | `"Star Wars: A New Hope"` |

## Gold list — surprising cases (where my prediction was WRONG or the result is non-obvious)

Verified by running the original code. Use these as tricky inputs in Step 4.

| Input | Actual output | Why it is surprising |
|-------|---------------|----------------------|
| `"mcdonald-smith"` | `"McDonald-Smith"` | **Predicted wrong.** The Mc rule titlecases the rest again, so the hyphen rule also runs on `donald-smith`. |
| `"DR SMITH"` | `"DR Smith"` | **Predicted wrong.** The Mr/Dr rule never lowercases the rest, even on an all-caps line. |
| `"hello the "` | `"Hello the "` | A trailing space makes the last "word" empty, so `the` is **not** capitalized as the last word. |
| `"the u.s. army"` | `"The u.s. Army"` | Lowercase initials are kept as written (inline-period rule). |
| `"the tv show"` | `"The Tv Show"` | The all-consonant rule needs 3+ letters. |
| `"psst nth cwm xyz"` | `"PSST NTH CWM Xyz"` | `y` counts as a vowel, so `xyz` is not an acronym. |
| `"see http://foo now"` | `"See Http://foo Now"` | `//` turns off the slash rule and there is no inline period, so the word just gets its first letter capitalized. |
| `"http://example.com"` | `"http://example.com"` | …but with a `.` between letters it is kept as written. |
| `"AND/OR"` | `"And/Or"` | All-caps line + slash + first/last capitalization. |
| `"macdonald"` | `"Macdonald"` | Only `Mc` is special, not `Mac`. |
| `"OLD MCDONALD"` | `"Old McDonald"` | `MC` is recognized in all-caps lines. |
| `"hello\r\nworld"` | `"Hello\nWorld"` | `\r\n` becomes `\n`. |
| `"iPhone-case"` | `"iPhone-case"` | The uppercase-elsewhere check runs before the hyphen split, so the whole word is kept. |
| `"what in?! the"` | `"What In?! The"` | `in?!` is not a small word (it has punctuation attached), so it gets capitalized. |
| `"e.g. this"` | `"e.g. This"` | Inline period: the first word is kept lowercase. |
| `"2001: A SPACE ODYSSEY"` | `"2001: A Space Odyssey"` | All caps: `A` → `a` (small word) → `A` again (sub-phrase rule). |
| `"hello: and goodbye"` | `"Hello: And Goodbye"` | Sub-phrase rule. |
| `"ÉCOLE NORMALE"` | `"École Normale"` | Non-ASCII letters work (`\w` is Unicode-aware). |
| `"hello the world"` | `"Hello the World"` | NBSP counts as whitespace and is kept in the output. |

## Not part of the port

- `callback`, `small_first_last`, `preserve_blank_lines` and `normalise_space_characters`
  are function options. The Go program only needs to match the **default call**,
  `titlecase(line)`.
- `create_wordlist_filter_from_file` / `cmd()` (CLI + `~/.titlecase.txt`) are not used.
- `titlecase/tests.py` is the upstream test suite.
