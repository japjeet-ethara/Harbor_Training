# titlecase notes

Facts below come from `titlecase/__init__.py` at the commit recorded here, and from `LICENSE.txt`. Example outputs were produced by calling `titlecase()`.

## Repository

- Repository URL: https://github.com/ppannuto/python-titlecase
- Git commit SHA: `42f43e2de55bf003b286c6f8e8d8b2d26676a167`
- Commit date: 2024-04-05 22:03:59 -0700
- License: The MIT License (MIT)

`LICENSE.txt` begins with “The MIT License (MIT)”. The module docstring points at the same MIT license.

## How `titlecase()` walks the text

`titlecase(text, callback=None, small_first_last=True, preserve_blank_lines=False, normalise_space_characters=False)` handles one line at a time, then one whitespace-separated word at a time. For each word it stops at the first matching rule. Small words, from the `SMALL` pattern, are:

`a`, `an`, `and`, `as`, `at`, `but`, `by`, `en`, `for`, `if`, `in`, `of`, `on`, `or`, `the`, `to`, `v`, `v.`, `via`, `vs`, `vs.`

A line counts as all capitals when `line.upper() == line`.

## Rules

1. **Collapse line breaks by default.** The text is split on one or more `\r` or `\n` characters, so a blank line is dropped. Processed lines are joined back with `\n`.
   - Input: `Line number one\n\nand Line three\n`
   - Output: `Line Number One\nAnd Line Three\n`

2. **Keep blank lines when asked.** With `preserve_blank_lines=True`, the split is on every single `\r` or `\n`, so empty lines stay in the result.
   - Input: `Line number one\n\nand Line three\n` (`preserve_blank_lines=True`)
   - Output: `Line Number One\n\nAnd Line Three\n`

3. **Keep the original whitespace characters by default.** Each line is split on individual whitespace characters (`\s`), and those same characters are placed back between the processed words.
   - Input: `text\twith\ttabs`
   - Output: `Text\tWith\tTabs`

4. **Normalize whitespace when asked.** With `normalise_space_characters=True`, the processed words are joined with a single ordinary space.
   - Input: `text\twith\ttabs` (`normalise_space_characters=True`)
   - Output: `Text With Tabs`

5. **A callback can replace a word.** If `callback(word, all_caps=...)` returns a truthy value, that value is used as the word. It is marked immutable, so the later first-word and last-word small-word capitalization leaves it alone. A falsy return continues with the rules below.
   - Input: `of mice and men` (callback returns `of` for `of`, and a falsy value otherwise)
   - Output: `of Mice and Men`

6. **Keep dotted initials on an all-capital line.** If the line is all capitals and the word matches `UC_INITIALS` (one or more pieces of the form `X.` or `X.Y`, where `X` and `Y` are uppercase letters), the word is copied through unchanged.
   - Input: `D.C.`
   - Output: `D.C.`

7. **Reshape `d'…` and `l'…` words.** If the word matches `APOS_SECOND` (`d`, `o`, or `l`, then `'` or `‘`, then letters, with an optional two-character ending made from `'` and `s`) and the first character is not a vowel, the first character is lowercased, the apostrophe stays, and the next letter is uppercased. The remainder of the word is not changed.
   - Input: `l'grange`
   - Output: `l'Grange`

8. **Reshape `o'…` words.** The same `APOS_SECOND` match with a vowel as the first character uppercases the first character and the letter after the apostrophe. The remainder of the word is not changed.
   - Input: `o'grange`
   - Output: `O'Grange`

9. **Capitalize an `Mc` prefix and title-case the rest.** `MAC_MC` matches `Mc`, `mc`, or `MC` followed by at least two word characters. The prefix is passed through `str.capitalize()` (`MC` becomes `Mc`) and the remainder is passed back through `titlecase()` with `small_first_last=True`.
   - Input: `mcclelland`
   - Output: `McClelland`

10. **Uppercase only the first letter of Mr, Mrs, Ms, and Dr.** `MR_MRS_MS_DR` matches `mr`, `mrs`, `ms`, and `dr` without regard to case. The first character is uppercased and the rest of the word stays as it was.
    - Input: `dr`
    - Output: `Dr`

11. **Keep a word that contains an internal period.** If `INLINE_PERIOD` finds a letter, a period, and another letter inside the word, the word is copied through unchanged.
    - Input: `this is just an example.com`
    - Output: `This Is Just an example.com`

12. **Keep a word that already has an uppercase letter later in it, when the line is not all capitals.** `UC_ELSEWHERE` matches optional leading punctuation, then letters, then an uppercase letter. This match is applied only when the line is not all capitals.
    - Input: `iTunes should be unmolested`
    - Output: `iTunes Should Be Unmolested`

13. **Lowercase a small word.** If the whole word matches `SMALL_WORDS`, it is written in lowercase. First and last position are adjusted later by rules 18 and 19.
    - Input: `this v that`
    - Output: `This v That`

14. **Title-case each piece of a slash word, except `//`.** If the word contains `/` and does not contain `//`, it is split on `/`. Each piece is passed through `titlecase()` with `small_first_last=False`, then the pieces are joined with `/`.
    - Input: `a title and/or string`
    - Output: `A Title and/or String`

15. **Title-case each piece of a hyphenated word.** If the word contains `-`, it is split on `-`. Each piece is passed through `titlecase()` with `small_first_last=False`, then the pieces are joined with `-`.
    - Input: `end-to-end`
    - Output: `End-to-End`

16. **Lowercase words from an all-capital line before the final casing steps.** When the line is all capitals, the word is lowercased before the consonant-acronym test and the ordinary first-letter capitalization. Earlier rules (initials, apostrophes, `Mc`, honorifics, and internal periods) still run on the original word.
    - Input: `THIS IS A TEST`
    - Output: `This Is a Test`

17. **Uppercase an all-consonant word longer than two letters.** Consonants here are the ASCII letters except `a`, `e`, `i`, `o`, `u`, and `y`. If the word is made only of those consonants and its length is greater than 2, the whole word is uppercased.
    - Input: `cnn`
    - Output: `CNN`

18. **Capitalize the first letter of any remaining word.** `CAPFIRST` uppercases the first letter. Punctuation in `PUNCT` before that letter stays in place. The rest of the word is left as it is. A word that does not match, such as one that starts with a digit, is left unchanged (`34th` stays `34th`).
    - Input: `(hello)`
    - Output: `(Hello)`

19. **Capitalize a small word at the start of the line.** When `small_first_last` is true and the first word was not fixed by the callback, `SMALL_FIRST` capitalizes a small word at the start, including when punctuation from `PUNCT` precedes it.
    - Input: `a thing`
    - Output: `A Thing`

20. **Capitalize a small word at the end of the line.** When `small_first_last` is true and the last word was not fixed by the callback, `SMALL_LAST` capitalizes a small word at the end. One trailing character from `PUNCT` is included in that capitalization.
    - Input: `Small word at end is nothing to be afraid of`
    - Output: `Small Word at End Is Nothing to Be Afraid Of`

21. **Capitalize a small word that opens a subphrase.** After the line is joined, `SUBPHRASE` finds a small word that follows a space and one of `: . ; ? ! - – ‒ — ―`, and capitalizes that small word.
    - Input: `Starting Sub-Phrase With a Small Word: a Trick, Perhaps?`
    - Output: `Starting Sub-Phrase With a Small Word: A Trick, Perhaps?`
