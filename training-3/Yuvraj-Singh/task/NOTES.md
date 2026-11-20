# python-titlecase notes

- Source: https://github.com/ppannuto/python-titlecase
- Commit: `42f43e2de55bf003b286c6f8e8d8b2d26676a167` (2024-04-05)
- Licence: MIT (`LICENSE.txt`, Copyright (c) 2021 Patrick William Pannuto)
- Answers were frozen by executing `titlecase()` with the stdlib `re` fallback. The optional third-party `regex` package is not installed, so Unicode property classes are not used.
- Those answers were produced by the stdlib `re` path of python-titlecase at commit `42f43e2de55bf003b286c6f8e8d8b2d26676a167`.
- Test data is ASCII only; Unicode is a possible hardening idea.
- Every test line is changed by `titlecase()`. A line that `titlecase()` would leave as-is is discarded and replaced from the same seeded generator.
- SHA256 of the frozen files: `inputs.txt` `BAA61DC1B4410C07C97F44C47FEA521430FE36DD5234F265A20BA212ED8EF984`, `expected.txt` `07D52956F4CBC21B6DA101784CE47CE66EFC0BCBBFE0533A6748A4F4BF5FFFA9`, `hidden_inputs.txt` `8489B5E691350914F90B474E1643403ECE205F931619DACD1159C8344C202A10`, `hidden_expected.txt` `1F519446FB718CE7BCE7FF3374DD7272AE37FD1D23F504C8CF8F3A8BC477E86B`.

## Rules `titlecase()` applies

1. Small words (`a`, `an`, `and`, `as`, `at`, `but`, `by`, `en`, `for`, `if`, `in`, `of`, `on`, `or`, `the`, `to`, `v`, `v.`, `via`, `vs`, `vs.`) are lowercased in the middle of a line. `the lord of the rings` → `The Lord of the Rings`.
2. A small word at the start or end of the line is capitalized. `small word at end is nothing to be afraid of` → `Small Word at End Is Nothing to Be Afraid Of`.
3. After `:`, `.`, `;`, `?`, `!`, or a dash plus a space, a lowercase small word is capitalized. `Starting Sub-Phrase With a Small Word: a Trick, Perhaps?` → `Starting Sub-Phrase With a Small Word: A Trick, Perhaps?`. This pattern is case-sensitive.
4. A run of ASCII letters that contains an uppercase letter after its first character is left unchanged, but only when that run is at the start of the word (optional leading punctuation). `iTunes should be unmolested` → `iTunes Should Be Unmolested`.
5. Words with an internal period between word characters are left unchanged, which keeps URLs and hostnames. `this is http://foo.com` → `This Is http://foo.com`.
6. An all-caps line is lowercased before the normal rules, except uppercase initials such as `D.C.`. `WASHINGTON, D.C. SHOULD BE FIXED BUT MIGHT BE A PROBLEM` → `Washington, D.C. Should Be Fixed but Might Be a Problem`.
7. `Mc`/`MC` prefixes are normalized to `Mc` and the remainder is title-cased, including through hyphens and slashes. `mcfoo-bar` → `McFoo-Bar`.
8. `mr`, `mrs`, `ms`, and `dr` keep their tail and only force the first letter up. `mr` → `Mr`, while `MR` stays `MR`. `Mss` is not one of these; as an all-consonant word longer than two letters it becomes `MSS`.
9. Apostrophe forms `d'…`, `o'…`, and `l'…` (ASCII `'` or `‘`) capitalize the letter after the apostrophe and do not rewrite the tail. `o'reilly` → `O'Reilly`, `l'GranGe` → `l'GranGe`.
10. Hyphenated and slash-separated words are title-cased per segment, unless the word contains `//`. `word/word` → `Word/Word`. `and/or` in the middle stays `and/or`.
11. A word of more than two ASCII consonants (y counts as a vowel) becomes uppercase. `cnn` → `CNN`. `st` stays short and becomes `St`.
12. The first word character is capitalized after any leading punctuation. Original spacing, including NBSP and other Unicode spaces, is preserved. `a mix of	different` keeps the NBSP and the tab.
