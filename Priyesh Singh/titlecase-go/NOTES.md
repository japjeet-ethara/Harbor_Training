# python-titlecase

- Repository: https://github.com/ppannuto/python-titlecase
- Commit: `42f43e2de55bf003b286c6f8e8d8b2d26676a167`
- Commit date: 2024-04-05T22:03:59-07:00
- License: MIT (`LICENSE.txt`)
- Package version in source: 2.4.1
- Answer sheets call `titlecase()` with its defaults. The optional `regex` extra is not installed, so the standard-library `re` patterns are the ones the Go port matches.

Rules below were checked by running `titlecase()` from that commit.

1. Small words stay lowercase in the middle, and the first and last words are capitalized. Small words: a, an, and, as, at, but, by, en, for, if, in, of, on, or, the, to, v, v., via, vs, vs.
   - `the lord of the rings` → `The Lord of the Rings`
2. `v` and `vs` stay small, with or without a period.
   - `this v. that` → `This v. That`
3. A word of only consonants, longer than two letters, becomes uppercase.
   - `Words with all consonants like cnn are acronyms` → `Words With All Consonants Like CNN Are Acronyms`
4. A token that contains a letter or digit, a period, and another letter or digit is left unchanged. `//` is not split on `/`.
   - `this is http://foo.com` → `This Is http://foo.com`
5. `Mc` or `MC` plus at least two more characters keeps that prefix and title-cases the rest. `Mac` is not a special prefix.
   - `Mr McTavish went to MacDonalds` → `Mr McTavish Went to MacDonalds`
6. `Mr`, `Mrs`, `Ms`, and `Dr` keep a capital first letter and the rest of their spelling.
   - `mr mrs ms dr` → `Mr Mrs Ms Dr`
7. A word matching `d`, `o`, or `l`, an apostrophe, then more letters, capitalizes the letter after the apostrophe. `o` is also capitalized; `d` and `l` stay lowercase.
   - `my name is o'reilly` → `My Name Is O'Reilly`
   - `l'grange l'grange` → `l'Grange l'Grange`
8. An all-caps line is lowercased before the other rules, except strings of initials such as `D.C.`, which stay as written.
   - `WASHINGTON, D.C. SHOULD BE FIXED BUT MIGHT BE A PROBLEM` → `Washington, D.C. Should Be Fixed but Might Be a Problem`
9. A small word after `:`, `;`, `.`, `?`, `!`, or a dash, plus a space, is capitalized.
   - `Starting Sub-Phrase With a Small Word: a Trick, Perhaps?` → `Starting Sub-Phrase With a Small Word: A Trick, Perhaps?`
10. A word that already has an internal ASCII capital is left unchanged. Hyphen and slash pieces are title-cased separately.
   - `iTunes should be unmolested` → `iTunes Should Be Unmolested`
11. On an all-caps line, non-ASCII letters are lowercased and then the first letter is capitalized. They are not treated as internal capitals.
   - `EL NIÑO A ARRIVÉ HIER` → `El Niño a Arrivé Hier`

Five lines in `tests/data/expected.txt` were checked again by calling `titlecase()` on the matching input line. They matched.
