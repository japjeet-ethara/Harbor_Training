# NOTES — python-titlecase

- Repo: https://github.com/ppannuto/python-titlecase
- Pinned commit (SHA, date): `42f43e2de55bf003b286c6f8e8d8b2d26676a167`  2024-04-05T22:03:59-07:00
- Licence: **MIT** (LICENSE.txt, Copyright (c) 2021 Patrick William Pannuto) -> allowed
- Source file: `titlecase/__init__.py` (function `titlecase`, ~293 lines)
- Mode used for the reference answers: the optional `regex` module IS installed
  (REGEX_AVAILABLE=True, so `\p{Letter}` / `\p{Uppercase_Letter}` are Unicode-aware).

## Rules applied by `titlecase(text)` (in the order the code applies them)

All examples below were run against the original code (not guessed).

1. **Line split.** Input is split on `[\r\n]+` (blank lines dropped); lines joined with `\n`.
   `'read this\n\nand that'` -> `'Read This\nAnd That'`
2. **Whitespace kept.** Line is split on single `\s` chars; the original space chars are kept.
   `'  leading and  double  spaces  '` -> `'  Leading and  Double  Spaces  '`
3. **ALL-CAPS line.** If `line.upper() == line`, the line is "all caps": words are lower-cased first, then capitalised.
   `'THE QUICK BROWN FOX'` -> `'The Quick Brown Fox'`
4. **Initials in an all-caps line** (`A.`, `A.B.` repeated) are left alone.
   `'J.R.R. TOLKIEN WROTE'` -> `'J.R.R. Tolkien Wrote'`
5. **Apostrophe-second words** `^[dol]['‘]\p{L}+(?:['s]{2})?$` (case-insens.): 3rd char upper-cased;
   1st char lower-cased if it is a consonant, upper-cased if it is a vowel (`o`).
   `"o'neil and d'artagnan and l'amour"` -> `"O'Neil and d'Artagnan and l'Amour"`
6. **Mc / Mac prefix** `^([Mm]c|MC)(\w.+)`: prefix capitalised, rest titlecased recursively. ("Mac" is NOT special.)
   `'mcdonald and macarthur'` -> `'McDonald and Macarthur'`;  `'MCDONALD'` -> `'McDonald'`
7. **Mr / Mrs / Ms / Dr** (case-insens.): first letter upper, rest unchanged, no period added.
   `'dr smith and mr jones and mrs lee and ms kim'` -> `'Dr Smith and Mr Jones and Mrs Lee and Ms Kim'`
8. **Inline period / mixed caps are left untouched:** word containing `letter.letter`, or (not all-caps line)
   a word matching `UC_ELSEWHERE` (a letter followed by an uppercase letter somewhere).
   `'visit example.com for details'` -> `'Visit example.com for Details'`
   `'iPhone and eBay and iOS'` -> unchanged;   `'NASA launches a new rocket'` -> `'NASA Launches a New Rocket'`
   `'the u.s.a. is big'` -> `'The u.s.a. Is Big'`   (<- surprising: `is` gets capitalised)
9. **Small words** (a an and as at but by en for if in of on or the to v v. via vs vs.) are lower-cased.
   `'a tale of two cities'` -> `'A Tale of Two Cities'`
10. **Slash words** (contain `/` but not `//`): each part titlecased separately (small-first disabled).
    `'and/or either/or'` -> `'And/or Either/Or'`;   `'http://example.com//path/x'` -> unchanged
11. **Hyphen words:** each part titlecased separately.
    `'state-of-the-art design'` -> `'State-of-the-Art Design'`
12. **All-consonant words longer than 2 letters** are upper-cased (acronym guess). `st` (len 2) is not.
    `'bcdfg are consonants'` -> `'BCDFG Are Consonants'`;  `'st louis is nice'` -> `'St Louis Is Nice'`
13. **Normal word:** first letter (after leading punctuation) upper-cased (CAPFIRST), rest unchanged.
    `"'quoted' and \"in\" the (parens) of"` -> `"'Quoted' and \"In\" the (Parens) Of"`
14. **First/last word of a line:** small words are capitalised (SMALL_FIRST / SMALL_LAST, with optional punctuation).
    `'stuff to look at'` -> `'Stuff to Look At'`;  `'to be or not to be'` -> `'To Be or Not to Be'`
15. **Sub-phrases:** after `: . ; ? ! - – ‒ — ―` + one space, a following small word is capitalised.
    `'what is this: a test; an example. the end'` -> `'What Is This: A Test; An Example. The End'`
16. **`v.` / `vs.`** are small words, but are capitalised at line start.
    `'v. the people vs. the state'` -> `'V. The People vs. The State'`
17. **Unicode letters** are handled as letters.  `'à la carte éclair über'` -> `'À La Carte Éclair Über'`

## Cases where my first expectation was WRONG (gold for the tests)
- `the u.s.a. is big` -> `is` is capitalised even though inline-period words stay lower.
- `macarthur` -> `Macarthur` (only Mc/MC are special).
- `and/or` -> `And/or` (small word `or` stays lower after the slash; `And` first-word rule).
- `(parens)` -> `(Parens)` but `the (parens) of` leaves `the` lower while last `of` becomes `Of`.
- `Dr`, `Mr` get no period; `st` stays `St` (too short for acronym rule).
- `v.` at line start -> `V.`, but later `vs.` stays lower.
