# python-titlecase: notes for the Harbor task

- **Repo URL:** https://github.com/ppannuto/python-titlecase
- **Commit SHA:** 42f43e2de55bf003b286c6f8e8d8b2d26676a167
- **Commit date:** 2024-04-05T22:03:59-07:00
- **Version:** 2.4.1
- **Licence:** MIT (`LICENSE.txt`, "The MIT License (MIT)", Copyright (c) 2021 Patrick William Pannuto). Allowed.

## Which code path is the reference

`titlecase/__init__.py` tries `import regex` and falls back to stdlib `re`.
The two branches use different patterns, so they give different answers on
non-ASCII text. This task uses the **stdlib `re` fallback** (`regex` not
installed), CPython 3.12, default arguments, no callback/wordlist.

## Rules, in the order the code applies them

All examples below were executed against the real code (`re` branch).

| # | Rule | Input | Output |
|---|------|-------|--------|
| 1 | Text is split on runs of `\r`/`\n`; lines are rejoined with `\n` | `one\r\n\r\ntwo` | `One\nTwo` |
| 2 | Each line is split on single `\s` chars; the original spacing is preserved | `the  quick\tfox` | `The  Quick\tFox` |
| 3 | A line is "all caps" when `line.upper() == line`; its words are lowered first | `THE QUICK BROWN FOX` | `The Quick Brown Fox` |
| 4 | On all-caps lines, initials are kept as they are | `THE C.I.A. FILES` | `The C.I.A. Files` |
| 5 | Apostrophe second letter (`d`/`o`/`l` + `'` or `‘`): consonant first letter is lowered, vowel is raised, third char is raised | `d'angelo` / `o'reilly` | `d'Angelo` / `O'Reilly` |
| 6 | Mc/MC prefix: `Mc` + recursive titlecase of the rest (not `Mac`) | `mcdonald` / `macdonald` | `McDonald` / `Macdonald` |
| 7 | mr/mrs/ms/dr: only the first letter is raised, the rest stay as typed | `mRS jones` | `MRS Jones` |
| 8 | A letter-dot-letter inside a word leaves the word alone | `example.com is down` | `example.com Is Down` |
| 9 | Mixed case (uppercase after a letter) leaves the word alone, unless the line is all caps | `iPhone sales` | `iPhone Sales` |
| 10 | Small words are lowered (a, an, and, as, at, but, by, en, for, if, in, of, on, or, the, to, v, v., via, vs, vs.) | `the lord of the rings` | `The Lord of the Rings` |
| 11 | `/` without `//`: each part is titlecased recursively, with no first/last small-word capitalising | `this and/or that` | `This and/or That` |
| 12 | `-`: each part is titlecased recursively, same way | `step-by-step guide` | `Step-by-Step Guide` |
| 13 | All-consonant word (y counts as a vowel) longer than 2 chars becomes upper case | `xml parser` / `st louis` | `XML Parser` / `St Louis` |
| 14 | Otherwise: raise the first letter after leading punctuation | `"hello" (world)` | `"Hello" (World)` |
| 15 | The first word of a line, if small, is capitalised, even after punctuation | `"the beginning" of it` | `"The Beginning" of It` |
| 16 | The last word of a line, if small, is capitalised, with at most one trailing punctuation char | `what is it for?` | `What Is It For?` |
| 17 | A small word after `: . ; ? ! - – ‒ — ―` plus a space is capitalised | `star wars: a new hope` | `Star Wars: A New Hope` |

## Rare cases (gold list)

Predictions I made from reading the code that were **wrong** when run:

1. `O'REILLY` stays `O'REILLY`, not `O'Reilly`. Rule 5 fires before all-caps
   lowering, and it only touches the first three characters.
2. `STRASSE AND straße` stays `STRASSE AND Straße`, not `Strasse and Straße`.
   `ß`.upper() is `SS`, so the line is not all caps, and `STRASSE` is then
   protected by rule 9.

Surprises that matched a careful reading, and will break a naive port:

3. A trailing space hides the last word: `what is it for ` gives
   `What Is It for ` (the last "word" is the empty string).
4. `ﬁsh` becomes `FIsh`: Python's `upper()` expands the ligature to two letters.
5. `ΟΔΟΣ ΤΟΥ` becomes `Οδος Του`: Python's `lower()` uses final sigma.
6. `and/or` alone gives `And/Or`, but in the middle of a line gives `and/or`.
7. `mc` gives `Mc`: rule 6 needs at least two more characters, so this goes
   down the normal path.
8. `\s` in Python covers `\x1c`-`\x1f`, `\x85`, NBSP and Unicode spaces. Go's
   `\s` is ASCII only and `unicode.IsSpace` omits `\x1c`-`\x1f`.

## Checked by hand

`python -c "from titlecase import titlecase; print(titlecase('the lord of the rings'))"`
prints `The Lord of the Rings`. All table rows and the 54 predictions were run
the same way; 52 matched and the 2 misses are listed above.
