# NOTES — python-titlecase

- Repo: https://github.com/ppannuto/python-titlecase
- Commit (HEAD when cloned): `42f43e2de55bf003b286c6f8e8d8b2d26676a167` — committed 2024-04-05T22:03:59-07:00
- Licence: **MIT** (LICENSE.txt, Copyright (c) 2021 Patrick William Pannuto) → allowed
- Package version: 2.4.1 (`titlecase/__init__.py`, 293 lines, single `titlecase()` function + helpers)
- Python used for ground truth: 3.12.3, `regex` module 2026.11.9 installed → `REGEX_AVAILABLE = True`
  (without `regex` the module falls back to `re` with different Unicode behaviour; ground truth is generated with `regex`)

## Rules applied by `titlecase()` (every example below was produced by running the original code)

1. **Lines and whitespace** — Input is split on runs of CR/LF. Inside a line, every single whitespace character is kept exactly (double spaces, tabs, leading and trailing spaces survive). Empty "words" between spaces are left empty.
   - `'foo  bar\tbaz'` → `'Foo  Bar\tBaz'`
   - `' the end '` → `' the End '`
2. **All-caps line** — If the whole line equals its own upper-case form, each word is lower-cased first and then capitalised. All-caps initials like J.R.R. are kept.
   - `'THE QUICK BROWN FOX'` → `'The Quick Brown Fox'`
   - `'THE J.R.R. TOLKIEN STORY'` → `'The J.R.R. Tolkien Story'`
3. **Small words stay lower case** — a an and as at but by en for if in of on or the to v v. via vs vs. (any case) are lower-cased when in the middle.
   - `'the lord of the rings'` → `'The Lord of the Rings'`
   - `'vs. the world v. them'` → `'Vs. The World v. Them'`
4. **First and last word always capitalised** — SMALL_FIRST / SMALL_LAST re-capitalise a small word at the start or end of the line, even behind punctuation. Only the first and last *token* are checked.
   - `'a tale of two cities'` → `'A Tale of Two Cities'`
   - `'going to the end of'` → `'Going to the End Of'`
   - `'(the) "quoted" word'` → `'(The) "Quoted" Word'`
5. **Inline period = leave alone** — A word with letter.letter inside (URLs, file names, j.r.r.) is returned unchanged.
   - `'visit www.example.com for details'` → `'Visit www.example.com for Details'`
   - `'j.r.r. tolkien'` → `'j.r.r. Tolkien'`
6. **Capital after first letter = leave alone** — If a word has an upper-case letter after its first letter (iPhone, eBay, NASA) it is returned unchanged, unless the whole line is upper case.
   - `'read iPhone and eBay reviews'` → `'Read iPhone and eBay Reviews'`
   - `'NASA launches new rocket'` → `'NASA Launches New Rocket'`
7. **d' / o' / l' names** — Words like o'neil, d'artagnan, l'amour: the letter after the apostrophe is upper-cased; d and l stay lower, o is upper.
   - `"o'neil and d'artagnan"` → `"O'Neil and d'Artagnan"`
   - `"l'amour is d'arcy's"` → `"l'Amour Is d'Arcy's"`
8. **Mc / MC prefix** — mc/Mc/MC + 2 more characters: rebuilt as 'Mc' + titlecase(rest). 'mac' is NOT special.
   - `'mcdonald and macdonald and MCDONALD'` → `'McDonald and Macdonald and McDonald'`
9. **Mr / Mrs / Ms / Dr** — Whole-word match in any case: first letter upper-cased, the rest unchanged.
   - `'mr smith and dr jones and mrs brown'` → `'Mr Smith and Dr Jones and Mrs Brown'`
   - `'MR smith and dR jones'` → `'MR Smith and DR Jones'`
10. **Slash words** — A word containing '/' (but not '//') is split, each part is titlecased with first/last-word handling OFF, and re-joined.
   - `'either/or and and/or'` → `'Either/or and and/Or'`
   - `'24/7 w/o a/b/c'` → `'24/7 W/O a/B/C'`
11. **Hyphen words** — A word containing '-' is split on '-', each part titlecased (first/last handling OFF), re-joined.
   - `'state-of-the-art design'` → `'State-of-the-Art Design'`
   - `'well-known x-ray e-mail'` → `'Well-Known X-Ray E-Mail'`
12. **All-consonant words** — A word of 3+ ASCII letters with no a/e/i/o/u/y is upper-cased as an acronym. 'y' counts as a vowel here, so nyc is NOT upper-cased.
   - `'html css and tv'` → `'HTML CSS and Tv'`
   - `'rhythm of the nyc fbi'` → `'Rhythm of the Nyc Fbi'`
13. **Sub-phrases** — After one of : . ; ? ! - – ‒ — ― followed by one space, a word that STARTS with a small word is capitalised (case-sensitive, no word boundary!).
   - `'hello: the world; an end'` → `'Hello: The World; An End'`
   - `'what is this? a test'` → `'What Is This? A Test'`
   - `'x. about this'` → `'X. About This'`
   - `'x: inner part'` → `'X: Inner Part'`
14. **Leading punctuation** — Capitalisation skips leading punctuation from the PUNCT set; digits or unlisted characters stop it.
   - `'(the) "quoted" word'` → `'(The) "Quoted" Word'`
   - `'“curly” and ‘single’'` → `'“Curly” and ‘Single’'`
   - `'3d and 2nd'` → `'3d and 2nd'`
   - `'...and then'` → `'...And Then'`

## Quirks where the obvious guess is wrong (verified by running the original)

- `'rhythm of the nyc fbi'` → `'Rhythm of the Nyc Fbi'`
- `'and/or either/or'` → `'And/or Either/Or'`
- `'foo-of'` → `'Foo-Of'`
- `'x. v. the end'` → `'X. V. the End'`
- `'x: inner part'` → `'X: Inner Part'`
- `"THE D'ARTAGNAN"` → `"The d'ARTAGNAN"`
- `'mcand'` → `'McAnd'`
- `'A.B.C and J.R'` → `'A.B.C and J.R'`
- `'café au lait'` → `'Café Au Lait'`
- `'STORY OF THE'` → `'Story of The'`

Why each one bites a port:
- `nyc` → `Nyc`: the consonant list is a..z minus a,e,i,o,u,**y**.
- `and/or` in the *first* word only gets SMALL_FIRST; only the *last* word gets SMALL_LAST.
- `foo-of`: SMALL_LAST uses `\b`, and a hyphen is a word boundary, so the small word after the hyphen is capitalised.
- `x. v. the end`: the SUBPHRASE regex is greedy (`v\.?`) and non-overlapping, so the dot of `v.` is consumed and the following `the` is not capitalised.
- `x: inner part`: SUBPHRASE has no `\b`, so `in` matches the start of `inner`.
- `THE D'ARTAGNAN`: in an all-caps line the apostrophe rule still fires but keeps the tail upper case.
- `mcand`: Mc-recursion calls titlecase() with first/last handling ON, so the small word `and` is capitalised.

## Where Go's `regexp` (RE2) cannot be used
Python regex features used: `\b` after alternations, lazy quantifiers `*?`/`+?` combined with anchors, Unicode properties (`\p{Letter}`, `\p{Uppercase_Letter}`), case-insensitive flags on alternations, non-overlapping `sub` with callbacks. RE2 has no look-around or back-references and Go's `\b` is ASCII-only, so all of these are re-implemented as rune-level code in the oracle.

## Known limits of the ground truth (so the task is fair)
- Inputs: single-line UTF-8, whitespace only space/tab, letters ASCII or common accented Latin; no characters whose case mapping changes length (ß, ŉ, ǰ, ligatures) — Python and Go case-mapping differ there.
- Characters outside the PUNCT set (e.g. `’` U+2019, `<`, `=`, `>`, `^`) are NOT treated as punctuation by the original.

