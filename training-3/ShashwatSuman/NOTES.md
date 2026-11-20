# NOTES: python-titlecase

- Repository: https://github.com/ppannuto/python-titlecase
- Commit SHA: 42f43e2de55bf003b286c6f8e8d8b2d26676a167
- Commit date: 2024-04-05T22:03:59-07:00
- Licence: MIT (`LICENSE.txt`), allowed for the task
- All logic is in `titlecase/__init__.py`, function `titlecase(text, ...)`.

Important: `pyproject.toml` does not declare the `regex` package. Without it, the
library silently falls back to Python's `re` and uses different patterns
(`\w` instead of `\p{Letter}`), so the answers change. This task always runs
it with `regex` installed:

```
uv run --no-project --python 3.12 --with regex==2026.11.18 python -c "from titlecase import titlecase; print(titlecase('the lord of the rings'))"
```

## Rules, in the order the code applies them to each word

Every example below was checked by running the original code.

1. **Line handling.** Text is split into lines on `\r`/`\n`, and each line into
   words on single whitespace characters. Spaces are kept exactly, so double
   spaces stay double. A line is "all caps" if `line.upper() == line`.
   `THE QUICK BROWN FOX` → `The Quick Brown Fox`
2. **Initials in an all-caps line stay as they are** (`U.`, `U.S.`, `J.R.R.`).
   `U.S. NEWS AND WORLD REPORT` → `U.S. News and World Report`
3. **Apostrophe after d / o / l** (`d'`, `o'`, `l'`, also with `‘`): the letter after
   the apostrophe is upper-cased. `o` becomes `O`, while `d` and `l` become lower case.
   `o'neil and d'artagnan` → `O'Neil and d'Artagnan`; `l'oreal ads` → `l'Oreal Ads`
4. **Mc / mc / MC prefix**: becomes `Mc` + titlecase of the rest (recursive).
   `mcdonald and macintosh` → `McDonald and Macintosh`; `MCDONALD` → `McDonald`
5. **Mr / Mrs / Ms / Dr** (any case): only the first letter is upper-cased.
   `mr smith meets dr jones` → `Mr Smith Meets Dr Jones`
6. **Left alone**: words with an inner period between letters, or (in a line
   that is not all caps) words with an upper-case letter after the first letter.
   `visit example.com today` → `Visit example.com Today`;
   `my iPhone and eBay` → `My iPhone and eBay`
7. **Small words** (a, an, and, as, at, but, by, en, for, if, in, of, on, or, the,
   to, v, v., via, vs, vs.) become lower case.
   `the lord of the rings` → `The Lord of the Rings`
8. **Slashes** (but not `//`): each part is titlecased on its own, and small words stay small.
   `and/or this/that` → `And/or This/That`;
   `http://example.com/path` → `http://example.com/path`
9. **Hyphens**: each part is titlecased on its own.
   `self-driving up-to-date` → `Self-Driving Up-to-Date`
10. **All-caps line**: the word is lower-cased before the next rules.
11. **All consonants and longer than 2 letters** become upper case (an acronym).
    `y` counts as a vowel. `rhythm pfft st nth` → `Rhythm PFFT St NTH`
12. **Normal word**: skip leading punctuation, upper-case the first letter.
    `"the end"` → `"The End"`
13. **First and last word**: a small word there is capitalised.
    `of mice and men` → `Of Mice and Men`; `the way out of` → `The Way Out Of`
14. **After `: . ; ? ! - – ‒ —` plus a space**, a following small word is capitalised.
    This is case-sensitive and has no word boundary.
    `title: a subtitle` → `Title: A Subtitle`;
    `part one - the start` → `Part One - The Start`;
    `vs. the world` → `Vs. The World`

## Surprises (the tricky cases to test)

- `nasa launches a rocket` → `Nasa Launches a Rocket`: NASA is NOT detected,
  because it has vowels.
- `straße` keeps `ß` because only the first letter is upper-cased, but `ß` in an
  upper-cased position becomes `SS` (Python's full Unicode upper-casing, which Go's
  `unicode.ToUpper` does not do).
- `title: android app` → `Title: Android App`: rule 14 matches the small word `a`
  at the start of `android`, with no word boundary.
- `vs. the world`: rule 14 fires after the period of `vs.`.
- `and/or` → `And/or`: slash parts are titlecased without first/last rules,
  then the whole line's first word gets rule 13.
