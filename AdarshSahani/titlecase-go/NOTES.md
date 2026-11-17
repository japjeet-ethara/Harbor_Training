# Python Titlecase — Implementation Notes

## 1. Source Repository

- Repository: `https://github.com/ppannuto/python-titlecase`
- Version: `2.4.1`
- Commit SHA: `42f43e2de55bf003b286c6f8e8d8b2d26676a167`
- Commit Date: `2024-04-05T22:03:59-07:00`
- Original implementation: Python
- Original algorithm: Based on John Gruber's Perl implementation.

## 2. Licence

The original project uses the MIT License.

Copyright (c) 2021 Patrick William Pannuto.

The MIT License permits use, modification, distribution, sublicensing, and sale, provided the copyright and permission notices are retained.

The software is provided without warranty.

## 3. Title-Case Rules

1. **Small words:** Words such as `a`, `an`, `and`, `as`, `at`, `but`, `by`, `for`, `if`, `in`, `of`, `on`, `or`, `the`, `to`, `via`, and `vs` are normally lowercase.
2. **First word:** A small word at the beginning of a title must be capitalized.
3. **Last word:** A small word at the end of a title must be capitalized.
4. **Punctuation:** Small words following punctuation and a space, such as a colon, semicolon, question mark, or hyphen, receive special capitalization.
5. **Existing capitalization:** Preserve words containing internal uppercase letters when the implementation identifies them as intentionally capitalized.
6. **Initialisms:** Preserve uppercase initials such as `U.S.A.` when the input line is entirely uppercase.
7. **Apostrophe prefixes:** Apply special handling to words beginning with `d'`, `o'`, and `l'`.
8. **Mc names:** Apply special capitalization to words beginning with `Mc`.
9. **Titles:** Special-case `Mr`, `Mrs`, `Ms`, and `Dr`.
10. **Inline periods:** Preserve words containing a letter-period-letter pattern, such as abbreviations.
11. **Slash-separated words:** Process slash-separated components recursively unless the word contains `//`.
12. **Hyphenated words:** Process each hyphen-separated component recursively.
13. **Consonant-only words:** Uppercase words containing only consonants when their length exceeds two characters. The letter `y` is treated as a vowel for this rule.
14. **All-uppercase input:** Detect all-uppercase lines and apply the implementation's uppercase normalization rules.
15. **Whitespace:** Preserve original whitespace by default.
16. **Blank lines:** Blank-line preservation depends on the `preserve_blank_lines` option.
17. **Unicode:** The implementation uses Unicode-aware regular expressions when the third-party `regex` package is available.
18. **Custom small-word list:** The implementation supports changing the small-word list through `set_small_word_list`.

## 4. Examples

| Input | Expected Output |
|---|---|
| `the lord of the rings` | `The Lord of the Rings` |
| `war and peace` | `War and Peace` |
| `a tale of two cities` | `A Tale of Two Cities` |
| `the art of war` | `The Art of War` |
| `hello: the world` | `Hello: The World` |
| `state-of-the-art` | `State-of-the-Art` |
| `mcdonald` | `McDonald` |
| `o'neil` | `O'Neil` |
| `dr smith` | `Dr Smith` |
| `north/south` | `North/South` |
| `NASA and HTML` | `NASA and HTML` |

## 5. Implementation Considerations

- Match the original Python implementation rather than relying on Go's built-in title-casing behaviour.
- Preserve punctuation and whitespace.
- Handle hyphens, slashes, apostrophes, abbreviations, and acronyms carefully.
- Go's standard regular-expression package does not support lookahead, lookbehind, or backreferences.
- Unicode handling must be considered separately from ASCII handling.
- The assignment's input/output contract is one title per input line, with one result per output line.