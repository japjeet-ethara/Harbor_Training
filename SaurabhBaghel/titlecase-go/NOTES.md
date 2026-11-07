# python-titlecase notes

- Repository: https://github.com/ppannuto/python-titlecase
- Commit: `42f43e2de55bf003b286c6f8e8d8b2d26676a167`
- Commit date: 2024-04-05T22:03:59-07:00
- Version constant in `titlecase/__init__.py`: 2.4.1
- Licence: MIT (`LICENSE.txt`, Copyright (c) 2021 Patrick William Pannuto)
- Vendored at `environment/repo` without `.git`
- Reference command: `titlecase(text)` with defaults (`callback=None`, `small_first_last=True`, `preserve_blank_lines=False`, `normalise_space_characters=False`)
- The task image installs `regex==2024.11.6`, so `REGEX_AVAILABLE` is true. Fixtures were frozen with that package. Do not treat the stdlib `re` fallback as the specification.

Small words, matched case-insensitively as a whole token: a, an, and, as, at, but, by, en, for, if, in, of, on, or, the, to, v, v., via, vs, vs.

## Rules

1. A normal word is capitalized on its first letter and the rest is left as-is.
   - `the lord of the rings` -> `The Lord of the Rings`
2. Small words stay lowercase in the middle of a line, and are capitalized when they are the first or last word.
   - `to be or not to be` -> `To Be or Not to Be`
   - `Small word at end is nothing to be afraid of` -> `Small Word at End Is Nothing to Be Afraid Of`
3. A line that is already entirely uppercase is lowered before the usual rules, except for initials and other early exceptions. An all-consonant token longer than two ASCII letters (y does not count as a consonant) becomes an acronym.
   - `THIS IS ALL CAPS AND SHOULD BE ADDRESSED` -> `This Is All Caps and Should Be Addressed`
   - `cnn` -> `CNN`
   - `NASA` -> `Nasa`, while `NASA rocket` -> `NASA Rocket` because the line is not all caps and the internal capitals are preserved
4. Tokens with an internal capital after the first letter, or with a letter-dot-letter sequence, are left unchanged. URLs that contain `//` are not split on `/`.
   - `iTunes should be unmolested` -> `iTunes Should Be Unmolested`
   - `this is just an example.com` -> `This Is Just an example.com`
   - `this is http://foo.com` -> `This Is http://foo.com`
5. A `/` splits a token when `//` is absent. Each piece is title-cased with first/last small-word capitalization turned off, then the outer token still capitalizes a leading or trailing small word.
   - `a title and/or string` -> `A Title and/or String`
   - `word/word` -> `Word/Word`
6. An ASCII hyphen splits the same way. En dashes and em dashes do not.
   - `a-b end-to-end two-not-three/three-by-four/five-and` -> `A-B End-to-End Two-Not-Three/Three-by-Four/Five-And`
   - `episode 7 – The force awakens` -> `Episode 7 – The Force Awakens`
7. `Mc` / `mc` / `MC` plus at least two more characters, the first of which is a word character, is rendered as `Mc` plus a recursive title-case of the remainder. `Mr`, `Mrs`, `Ms`, and `Dr` capitalize only the first letter.
   - `Mr McTavish went to MacDonalds` -> `Mr McTavish Went to MacDonalds`
   - `mcfoo-bar, MCFOO-BAR, McFoo-bar` -> `McFoo-Bar, McFoo-Bar, McFoo-Bar`
   - `mr` -> `Mr`
8. A leading `d`, `o`, or `l` followed by `'` or `‘` and a letter keeps that shape: `o` is uppercase, `d` and `l` are lowercase, and the first letter after the apostrophe is uppercase. An optional trailing `'s` is kept.
   - `my name is o'reilly` -> `My Name Is O'Reilly`
   - `l'grange` -> `l'Grange`
   - `o'grange's` -> `O'Grange's`
9. After the words are joined, a small-word prefix that follows `:`, `.`, `;`, `?`, `!`, or a dash plus a normal space is capitalized. Original whitespace, including tabs and non-breaking spaces, is preserved.
   - `Starting Sub-Phrase With a Small Word: a Trick, Perhaps?` -> `Starting Sub-Phrase With a Small Word: A Trick, Perhaps?`
   - `Mr. and Mrs. Person` -> `Mr. And Mrs. Person`
   - `a mix of	different` (nbsp and tab) keeps those space characters
10. All-caps initials made of `X.` groups, including a final `X.Y` pair, stay unchanged on an all-caps line.
    - `WASHINGTON, D.C. SHOULD BE FIXED BUT MIGHT BE A PROBLEM` -> `Washington, D.C. Should Be Fixed but Might Be a Problem`
    - `EPISODE 7 — THE FORCE AWAKENS` -> `Episode 7 — The Force Awakens`

Checked against `titlecase()` with `regex==2024.11.6` on 2026-11-06. The Go port in `solution/src` matched the library's own single-line cases and a 4,000-line fuzz set from seed 1.
