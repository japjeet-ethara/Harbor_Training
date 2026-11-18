# NOTES — python-titlecase (source for the `titlecase-go` task)

| Item | Value |
|---|---|
| Repo | https://github.com/ppannuto/python-titlecase |
| Commit SHA | `42f43e2de55bf003b286c6f8e8d8b2d26676a167` |
| Commit date | 2024-04-05T22:03:59-07:00 |
| Version | 2.4.1 (`titlecase/__init__.py`) |
| Licence | MIT (`LICENSE.txt`) — OK to use |
| Reference behaviour | `titlecase(line)` with defaults, **standard-library `re` only** (the optional `regex` extra is *not* installed, so `REGEX_AVAILABLE = False`) |

All examples below were produced by running the original code (Python 3.13, stdlib `re`).

## Rules applied by `titlecase()` (in the order the code applies them)

The line is split on every single whitespace character (`re.split(r'(\s)')`), each "word" is processed, then the words are re-joined with the *original* whitespace. A line is **all-caps** when `line.upper() == line` (so a line with no letters counts as all-caps).

1. **Upper-case initials kept (all-caps lines only).** `^(?:[A-Z]\.|[A-Z]\.[A-Z])+$` words stay as they are.
   `I.B.M. RULES` → `I.B.M. Rules`
2. **d' / o' / l' prefixes.** `^[dol]['‘]\w+(?:['s]{2})?$` (case-insensitive): third letter is upper-cased; first letter is lower for d/l, upper for o.
   `o'neil and d'artagnan` → `O'Neil and d'Artagnan`; `o'neil's` → `O'Neil's`
3. **Mc prefix.** `^([Mm]c|MC)(\w.+)` (needs 4+ chars): `Mc` + **recursive** `titlecase(rest)` (with first/last rule on).
   `MCDONALD'S` → `McDonald's`; `mcthe` → `McThe`; `mcd` → `MCD` (too short, falls to rule 10)
4. **Mr / Mrs / Ms / Dr** (any case, whole word): first letter upper-cased only.
   `mr smith and dr jones` → `Mr Smith and Dr Jones`
5. **Inline period → left alone.** `\w.\w` anywhere in the word.
   `visit example.com for info` → `Visit example.com for Info`; `e.g. this` → `e.g. This`
6. **Upper-case after the first letter → left alone (not on all-caps lines).** After any leading punctuation, the first run of ASCII letters has an upper-case letter after its first letter.
   `the iPhone and the iPad` → `The iPhone and the iPad`; `THE iPhone` → `The iPhone`
7. **Small words lower-cased.** `a an and as at but by en for if in of on or the to v v. via vs vs.` (whole word, any case).
   `the lord of the rings` → `The Lord of the Rings`
8. **Slashes.** If the word has `/` but not `//`, each part is titlecased **recursively with the first/last rule off**; URLs (`//`) fall through.
   `either/or` → `Either/or`; `foo/the/bar` → `Foo/the/Bar`; `http://foo.com/bar` unchanged
9. **Hyphens.** Same recursion on `-` parts. Each part decides "all-caps" on its own.
   `the well-known on-demand service` → `The Well-Known on-Demand Service`; `well-KNOWN fact` → `Well-Known Fact`
10. **All-caps line → word lower-cased first**, then:
11. **All-consonant acronym guess.** Only `[bcdfghjklmnpqrstvwxz]` (note: **y counts as a vowel**) and length > 2 → upper-case.
    `cnn and bbc reports` → `CNN and BBC Reports`; `xyz` → `Xyz`; `st louis` → `St Louis`
12. **Normal word.** Upper-case the first `\w` character that follows only punctuation characters. `\w` includes digits and `_`, so those "absorb" the capital.
    `1st place` → `1st Place`; `_foo bar` → `_foo Bar`
13. **First word / last word.** A small word at the start (after punctuation) or end (before at most one punctuation char) of the line is capitalised — but only if the very first/last *split element* is that word.
    `a tale of two cities` → `A Tale of Two Cities`; `what is it for` → `What Is It For`; `end-to` → `End-To`
14. **Sub-phrase.** A lower-case small word right after `: . ; ? ! - – ‒ — ―` + **one ASCII space** is capitalised (case-sensitive, no word boundary needed).
    `starting out: a guide to the end` → `Starting Out: A Guide to the End`; `vs. the world v. them` → `Vs. The World v. Them`
15. **Whitespace is preserved exactly** (tabs, double spaces, NBSP).
    `word\twith  tabs` → `Word\tWith  Tabs`

## Surprises (where a quick reading — or an agent — gets it wrong)

These are the rare cases the generator must hit:

- `' the end'` → `' the End'` — a leading space makes the first split element empty, so rule 13 never fires.
- `'the end '` → `'The End '` — same for the trailing side.
- `’tis` (U+2019) is **not** in the punctuation set, so `’tis the season` → `’tis the Season`; but `‘tis` (U+2018) **is**, so → `‘Tis the Season`.
- `x a.a` → `X a.A` — rule 5 keeps `a.a`, but rule 13 still capitalises the trailing `a`.
- `the.end` → `The.end`; `v.x` → `V.x`; `one v.` → `One V.` — the `\b` after `v.` only holds before a word character.
- `rock'n'roll` → `Rock'n'roll` (not an apostrophe-prefix word: first letter is `r`).
- `ÉCOLE DES BEAUX ARTS` → `École Des Beaux Arts` — `des`/`au` are not small words; accented letters are `\w`.
- `“the” end` → `“The” End` but `”` (U+201D) and `’` (U+2019) are not punctuation for these rules.
- `A.B.C. IS U.S.A.` → `A.B.C. Is U.S.A.` (rule 1 only applies when the whole line is upper case).
- `rhythm` → `Rhythm` (has a `y`, so not an acronym).
- With the optional `regex` package installed the behaviour differs (Unicode letter classes); the task freezes the stdlib-`re` behaviour.
