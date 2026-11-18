# Notes
Project: python-titlecase
Repository: https://github.com/ppannuto/python-titlecase
Commit SHA: 42f43e2de55bf003b286c6f8e8d8b2d26676a167 2024-04-05T22:03:59-07:00

## Licence

The MIT License (MIT)

## Rules applied by `titlecase`

The function title-cases each word and applies the following rules, in order.

1. **Blank lines are collapsed by default.** Runs of carriage returns and newlines are treated as one break, so an empty line disappears.
   - Input: `Line number one\n\nand Line three\n`
   - Output: `Line Number One\nAnd Line Three\n`

2. **Blank lines are kept when `preserve_blank_lines` is true.** Each line break is kept on its own.
   - Input: `Line number one\n\nand Line three\n` with `preserve_blank_lines=True`
   - Output: `Line Number One\n\nAnd Line Three\n`

3. **A callback result replaces the word and is left unchanged afterwards.** If `callback` returns a non-empty string, that string is used and later rules, including capitalising a small word at the start or end of the line, do not touch it.
   - Input: `afraid of` with a callback that returns `of` for that word
   - Output: `Afraid of`

4. **Dotted initials on an all-caps line are kept.** A word made of uppercase initials such as `A.B` or `A.B.` is copied through when the whole line is uppercase.
   - Input: `WASHINGTON, D.C. SHOULD BE FIXED BUT MIGHT BE A PROBLEM`
   - Output: `Washington, D.C. Should Be Fixed but Might Be a Problem`

5. **`d'` and `l'` words: the first letter stays lowercase and the letter after the apostrophe is capitalised.** The remainder of the word is kept as written. The apostrophe may be `'` or `‘`.
   - Input: `l'grange`
   - Output: `l'Grange`

6. **`o'` words: the first letter and the letter after the apostrophe are both capitalised.** The remainder of the word is kept as written. A possessive `'s` is allowed.
   - Input: `o'reilly`
   - Output: `O'Reilly`

7. **A `Mc` prefix is normalised to `Mc` and the rest of the word is title-cased.** This matches `Mc`, `mc`, or `MC` when at least two more characters follow. A `Mac` prefix is not treated this way.
   - Input: `mcclelland`
   - Output: `McClelland`

8. **`Mr`, `Mrs`, `Ms`, and `Dr` have only the first letter uppercased.** The rest of those words is left as it was, and the match is case-insensitive.
   - Input: `mr smith`
   - Output: `Mr Smith`

9. **A word that contains a letter, a period, and another letter is left unchanged.** This keeps domains and similar tokens intact.
   - Input: `this is just an example.com`
   - Output: `This Is Just an example.com`

10. **An existing internal capital is left unchanged when the line is not all caps.** A word that already has an uppercase letter after its opening letters is copied through.
    - Input: `iTunes should be unmolested`
    - Output: `iTunes Should Be Unmolested`

11. **Small words are lowercased.** The list, from the New York Times Manual of Style plus `vs` and `v`, is: a, an, and, as, at, but, by, en, for, if, in, of, on, or, the, to, v, v., via, vs, vs.
    - Input: `this v that`
    - Output: `This v That`

12. **A word split by a single slash is title-cased on each side of the slash.** `//` is not split. Small words inside those parts stay small unless a later first-or-last rule applies to the whole token.
    - Input: `word/word`
    - Output: `Word/Word`

13. **A double slash is not a split point.** Only the first letter of the whole token is capitalised.
    - Input: `foo//bar`
    - Output: `Foo//bar`

14. **A hyphenated word is title-cased on each side of the hyphen.** Small words in the middle stay lowercase.
    - Input: `end-to-end`
    - Output: `End-to-End`

15. **An all-caps line is lowercased before ordinary capitalisation.** Words still waiting to be cased are put into lowercase so the line becomes title case rather than staying in capitals. Initials already kept by rule 4 are not lowercased.
    - Input: `THIS IS ALL CAPS AND SHOULD BE ADDRESSED`
    - Output: `This Is All Caps and Should Be Addressed`

16. **A long all-consonant word is treated as an acronym.** If every letter is a consonant other than y, and the word is longer than two letters, the word is uppercased. `a`, `e`, `i`, `o`, `u`, and `y` do not count as consonants here, so a short word such as `st` is title-cased instead (`5th st` becomes `5th St`).
    - Input: `words like cnn`
    - Output: `Words Like CNN`

17. **Every other word has its first letter capitalised.** Leading punctuation is skipped, and a digit is left as a digit, so `34th 3rd 2nd` stays `34th 3rd 2nd`.
    - Input: `a thing`
    - Output: `A Thing`

18. **A small word at the start of the line is capitalised.** Leading punctuation stays in front of it. This step is skipped when `small_first_last` is false (as it is for the recursive slash and hyphen parts) and when a callback froze the word.
    - Input: `'by the Way, small word at the start but within quotes.'`
    - Output: `'By the Way, Small Word at the Start but Within Quotes.'`

19. **A small word at the end of the line is capitalised.** One trailing punctuation character is included in that capitalisation.
    - Input: `Small word at end is nothing to be afraid of`
    - Output: `Small Word at End Is Nothing to Be Afraid Of`

20. **A small word that opens a sub-phrase is capitalised.** After `:`, `.`, `;`, `?`, `!`, `-`, or a dash, plus a space, the following small word is capitalised.
    - Input: `Starting Sub-Phrase With a Small Word: a Trick, Perhaps?`
    - Output: `Starting Sub-Phrase With a Small Word: A Trick, Perhaps?`

21. **The original space characters are kept.** Tabs and other spaces stay between the words.
    - Input: `text\twith\ttabs`
    - Output: `Text\tWith\tTabs`

22. **Spaces are normalised when `normalise_space_characters` is true.** Words are joined with a single ordinary space.
    - Input: `text\twith\ttabs` with `normalise_space_characters=True`
    - Output: `Text With Tabs`

23. **Processed lines are joined with a newline.**
    - Input: `this shouldn't\nget mangled`
    - Output: `This Shouldn't\nGet Mangled`
