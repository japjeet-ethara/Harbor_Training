# python-titlecase

- Repository: https://github.com/ppannuto/python-titlecase
- Latest commit: `42f43e2de55bf003b286c6f8e8d8b2d26676a167`
- Commit date: 2024-04-05 22:03:59 -0700
- Package version in source: 2.4.1 (`titlecase/__init__.py`)

These notes describe `titlecase()` as implemented in `titlecase/__init__.py`. Examples below were produced by calling that function.

## Licence

**The MIT License (MIT)**

`LICENSE.txt` is the MIT License. Copyright (c) 2021 Patrick William Pannuto. The module docstring points at the same licence: http://www.opensource.org/licenses/mit-license.php

## How `titlecase()` walks the text

`titlecase(text, callback=None, small_first_last=True, preserve_blank_lines=False, normalise_space_characters=False)` handles one line at a time, then one whitespace-separated word at a time. For each word it tries the special cases in the order below. A `continue` after a match skips the remaining per-word rules. After every word on the line has been handled, it capitalises a small word at the start and at the end, joins the line, then capitalises a small word that opens a sub-phrase.

The implementation prefers the third-party `regex` module. If that import fails it falls back to the standard-library `re` module, and the Unicode letter classes (`\p{Letter}`, `\p{Uppercase_Letter}`) become ASCII `\w` / `[A-Z]`. The examples here ran with `regex` available.

Small words, matched case-insensitively as a whole word, are:

`a`, `an`, `and`, `as`, `at`, `but`, `by`, `en`, `for`, `if`, `in`, `of`, `on`, `or`, `the`, `to`, `v`, `v.`, `via`, `vs`, `vs.`

The docstring says this list comes from the New York Times Manual of Style, plus `vs` and `v`.

## Rules

1. **Blank lines are collapsed by default.** With `preserve_blank_lines=False`, the text is split on `[\r\n]+`, so consecutive line breaks become one break and empty lines disappear. Lines are joined back with `\n`.
   - Input: `Line number one\n\nand Line three\n`
   - Output: `Line Number One\nAnd Line Three\n`

2. **Blank lines are kept when `preserve_blank_lines` is true.** The split is then `[\r\n]`, one break at a time, so an empty line stays in the output. A Windows `\r\n` pair is two breaks under this pattern, so one `\r\n` becomes two `\n` characters in the result.
   - Input: `Line number one\n\nand Line three\n` with `preserve_blank_lines=True`
   - Output: `Line Number One\n\nAnd Line Three\n`

3. **The original space characters between words are kept by default.** Each line is split with `(\s)`, which keeps the separators. Words are rewritten; the original separators (spaces, tabs, non-breaking spaces, and other whitespace) are written back between them.
   - Input: `text\twith\ttabs`
   - Output: `Text\tWith\tTabs`

4. **`normalise_space_characters=True` replaces every separator run with a single ordinary space.** The processed words are joined with `" "` and the captured whitespace is discarded.
   - Input: `text\twith\ttabs` with `normalise_space_characters=True`
   - Output: `Text With Tabs`

5. **A line equal to its own uppercase form is an all-caps line.** `all_caps` is `line.upper() == line`. On that line, once the initials, apostrophe, Mc, and name-prefix checks have not matched, the word is lowercased before the acronym check and the ordinary capitalisation. `UC_ELSEWHERE` (rule 10) is not applied on an all-caps line, so an all-caps token is not preserved merely because it contains capitals.
   - Input: `THIS IS ALL CAPS AND SHOULD BE ADDRESSED`
   - Output: `This Is All Caps and Should Be Addressed`

6. **A truthy callback result replaces the word and is then left alone by the first-word and last-word passes.** The call is `callback(word, all_caps=all_caps)`. If the return value is truthy, it is stored as an `ImmutableString` or `ImmutableBytes` and the remaining per-word rules are skipped. `None` and `""` are ignored, and the normal rules run. The immutable mark blocks only the later small-word fixes at the start and end of the line. The sub-phrase pass in rule 18 still runs on the joined line.
   - Input: `the end`, with a callback that returns `the` unchanged for that word and returns `None` otherwise
   - Output: `the End`
   - Without that callback the same input is `The End`, because rule 16 capitalises the opening small word.

7. **On an all-caps line, uppercase initials are copied through unchanged.** The word must match `^(?:[Uppercase].[Uppercase] | [Uppercase].)+` for its whole length: either a single capital and a period, repeated, or a capital, a period, and one more capital. This check does not run when the line is mixed case.
   - Input: `A.B IS FINE`
   - Output: `A.B Is Fine`

8. **A word shaped like `d'…`, `l'…`, or `o'…` capitalises the letter after the apostrophe.** The whole word must match `^[dol]['‘][letters]+` with an optional trailing `'s` (two characters, each `'` or `s`). The apostrophe character is kept. If the first letter is not a vowel in `aeiouAEIOU` (`d` and `l`), it is forced to lowercase. If it is a vowel (`o`), it is uppercased. Characters after the capitalised third character are not recased.
   - Input: `l'grange`
   - Output: `l'Grange`
   - The vowel branch of the same rule turns `o'clock` into `O'Clock`.

9. **An `Mc` or `MC` prefix is normalised to `Mc`, and the remainder is titlecased again.** The word must match `^([Mm]c|MC)` plus at least two more word characters. `capitalize()` on the prefix yields `Mc`. The remainder is passed to `titlecase(..., small_first_last=True)`. A bare `Mc` or `MC` does not match, because the remainder is too short. `Mac` does not match this pattern.
   - Input: `mcdonald`
   - Output: `McDonald`

10. **`m`, `mr`, `mrs`, `ms`, and `dr` uppercase only the first character.** The word must match `^((m((rs?)|s))|Dr)$` with the case-insensitive flag, so the accepted forms are `m`, `mr`, `mrs`, `ms`, and `Dr` in any capitalisation. The new word is `word[0].upper() + word[1:]`, so the tail is not rewritten. A trailing period means this pattern does not match.
    - Input: `dr smith`
    - Output: `Dr Smith`

11. **A token with a letter, a period, and another letter inside it is left unchanged.** `INLINE_PERIOD` searches for that sequence anywhere in the word, so hostnames and similar tokens keep the casing they arrived with. With `regex` installed, “letter” is a Unicode letter; in the `re` fallback it is `\w`.
    - Input: `this is just an example.com`
    - Output: `This Is Just an example.com`

12. **On a line that is not all caps, a word that already contains an uppercase letter after its first letters is left unchanged.** `UC_ELSEWHERE` is optional leading punctuation, then one or more letters, then one or more uppercase letters. This is what keeps internal capitals such as `iTunes`, `macOS`, and `AT&T`.
    - Input: `iTunes should be unmolested`
    - Output: `iTunes Should Be Unmolested`

13. **A word that is exactly a small word is lowercased.** The match is the whole word, case-insensitive, against the list at the top of these notes. Rules 16, 17, and 18 may capitalise that word again if it is the first word, the last word, or the start of a sub-phrase. A small word in the middle stays lowercase, which is what `of` does in the example.
    - Input: `the lord of the rings`
    - Output: `The Lord of the Rings`

14. **A word that contains `/`, and does not contain `//`, is split on `/` and each piece is titlecased.** Each piece is recursive `titlecase` with `small_first_last=False`, then the pieces are joined with `/`. Because the first/last capitalisation is off for those pieces, a small word inside a slash pair stays lowercase. A `//` skips this rule entirely, so the token falls through to the later rules.
    - Input: `a title and/or string`
    - Output: `A Title and/or String`

15. **A word that contains an ASCII hyphen is split on `-` and each piece is titlecased.** This is checked only after the slash rule. Each piece uses `titlecase` with `small_first_last=False`, then the pieces are joined with `-`. Only the character `-` causes this split. The en dash, em dash, and the other dashes in the punctuation class do not.
    - Input: `state-of-the-art`
    - Output: `State-of-the-Art`

16. **A word of only consonants, longer than two characters, is uppercased as an acronym.** The consonant set is `string.ascii_lowercase` minus `a`, `e`, `i`, `o`, `u`, and `y`, tested case-insensitively from the start of the word to the end. `y` is treated as a vowel here, so it blocks this rule. Length is the raw word length and must be greater than 2, so `st` and `tv` are not acronyms (`St`, `Tv`). On an all-caps line this test runs after rule 5 has lowercased the word.
    - Input: `words with cnn inside`
    - Output: `Words With CNN Inside`

17. **Any word that none of the earlier rules took is capitalised at its first word character.** `CAPFIRST` matches optional leading punctuation and then one word character, and replaces that whole match with its uppercase form. The rest of the token is unchanged. A digit is a word character, so a token such as `34th` stays `34th` because uppercasing `3` does nothing and the following letters are not rewritten.
    - Input: `hello world`
    - Output: `Hello World`

18. **With `small_first_last` left at its default true, a small word at the start of the line is capitalised.** This runs only when the line produced at least one word and the first word is not an immutable callback result. Leading punctuation is kept, and the small word itself is `capitalize()`d. The pattern allows the small word to be the start of the first token, so punctuation before it does not hide it.
    - Input: `of mice and men`
    - Output: `Of Mice and Men`
    - With `small_first_last=False`, `the end` stays `the End`.

19. **With `small_first_last` true, a small word at the end of the line is capitalised.** The last word is skipped if a callback marked it immutable. The match is a small word at the end, plus at most one trailing punctuation character. `capitalize()` is applied to that whole match, so the small word’s first letter is uppercased and the rest of the match is lowercased.
    - Input: `nothing to be afraid of`
    - Output: `Nothing to Be Afraid Of`

20. **A small word after sub-phrase punctuation is capitalised on the joined line.** After words and spaces are joined, `SUBPHRASE` finds a small word that follows a space and one of `:`, `.`, `;`, `?`, `!`, `-`, `–`, `‒`, `—`, or `―`. That small word is `capitalize()`d. This still runs when a callback produced the small word, because it looks at the finished string rather than the immutable objects.
    - Input: `Starting Sub-Phrase With a Small Word: a Trick, Perhaps?`
    - Output: `Starting Sub-Phrase With a Small Word: A Trick, Perhaps?`
