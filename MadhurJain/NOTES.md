# Titlecase notes

Repo: https://github.com/ppannuto/python-titlecase
Commit: 42f43e2de55bf003b286c6f8e8d8b2d26676a167
Date: 2024-04-05T22:03:59-07:00

## Licence

The MIT License (MIT)

## Rules applied by `titlecase`

1. The text is handled one line at a time, and the lines are joined back with `\n`. A run of line breaks counts as a single break, so a blank line in the middle is dropped. A break at the very start or end still leaves one empty line.
   - Input: `Line number one\n\nand Line three\n`
   - Output: `Line Number One\nAnd Line Three\n`

2. With `preserve_blank_lines=True`, every line break is kept, including blank lines.
   - Input: `Line number one\n\nand Line three\n`
   - Output: `Line Number One\n\nAnd Line Three\n`

3. The original space characters between words are kept, including tabs and other Unicode spaces.
   - Input: `text\twith\ttabs`
   - Output: `Text\tWith\tTabs`

4. With `normalise_space_characters=True`, those separators are replaced by a single ordinary space.
   - Input: `text\twith\ttabs`
   - Output: `Text With Tabs`

5. If a callback returns a value for a word, that value is used as-is. The word is then left alone, including by the first-word and last-word rules below. A callback that returns nothing lets the other rules run.
   - Input: `the udp wrapper`, with a callback that returns `the` for “the” and `UDP` for “udp”
   - Output: `the UDP Wrapper`

6. When the whole line is already uppercase, a word of dotted initials is left unchanged. The word must be one or more groups of the form `A.` or `A.B`.
   - Input: `WASHINGTON, D.C. SHOULD BE FIXED BUT MIGHT BE A PROBLEM`
   - Output: `Washington, D.C. Should Be Fixed but Might Be a Problem`

7. A word that starts with `d`, `o`, or `l` and an apostrophe (`'` or `‘`) keeps that shape: the letter after the apostrophe is capitalized, `o` is capitalized, and `d` or `l` stays lowercase. An optional `'s` at the end is allowed.
   - Input: `o'grange`
   - Output: `O'Grange`

8. A word that starts with `Mc` or `MC`, followed by at least two more characters, keeps a capitalized `Mc` prefix. The remainder is title-cased on its own.
   - Input: `mcdonald`
   - Output: `McDonald`

9. `Mr`, `Mrs`, `Ms`, and `Dr` (any mix of case) have only the first letter forced to uppercase. The rest of the letters stay as written.
   - Input: `mrs`
   - Output: `Mrs`

10. A word that contains an internal period between two letters, such as a hostname, is left unchanged.
    - Input: `this is just an example.com`
    - Output: `This Is Just an example.com`

11. On a line that is not all uppercase, a word that already has a capital letter after its first letter is left unchanged. Leading punctuation may precede those letters.
    - Input: `iTunes should be unmolested`
    - Output: `iTunes Should Be Unmolested`

12. Small words are lowercased. The list, from the New York Times Manual of Style plus `vs` and `v`, is: a, an, and, as, at, but, by, en, for, if, in, of, on, or, the, to, v, v., via, vs, vs. Matching ignores case.
    - Input: `this v that`
    - Output: `This v That`

13. A word that contains `/` but not `//` is split on each `/`. Each piece is title-cased with the first-and-last small-word step turned off, then the pieces are joined with `/` again.
    - Input: `word/word`
    - Output: `Word/Word`

14. A hyphenated word is split on each `-`. Each piece is title-cased with the first-and-last small-word step turned off, then the pieces are joined with `-` again.
    - Input: `end-to-end`
    - Output: `End-to-End`

15. On a line that is entirely uppercase, a word that is still being processed is lowercased before the acronym and capitalization steps, so a shouted line becomes title case.
    - Input: `THIS IS ALL CAPS AND SHOULD BE ADDRESSED`
    - Output: `This Is All Caps and Should Be Addressed`

16. A word made only of consonants and longer than two letters is treated as an acronym and uppercased. `a`, `e`, `i`, `o`, `u`, and `y` count as vowels, so a short word such as `st` is not treated as an acronym.
    - Input: `words with all consonants like cnn are acronyms`
    - Output: `Words With All Consonants Like CNN Are Acronyms`

17. Any other word has its first letter capitalized. Punctuation before that letter stays in place, and the rest of the word is not changed. A word with no letter after optional leading punctuation, such as `34th`, is left unchanged.
    - Input: `'hello'`
    - Output: `'Hello'`

18. When `small_first_last` is true (the default), a small word at the start of the line is capitalized. Leading punctuation stays in front of it. A word fixed by a callback is skipped. Slash and hyphen pieces are title-cased with this step off.
    - Input: `'by the Way, small word at the start but within quotes.'`
    - Output: `'By the Way, Small Word at the Start but Within Quotes.'`

19. When `small_first_last` is true, a small word at the end of the line is capitalized. One trailing punctuation character may follow it. A word fixed by a callback is skipped.
    - Input: `Small word at end is nothing to be afraid of`
    - Output: `Small Word at End Is Nothing to Be Afraid Of`

20. After the words are joined, a small word that starts a sub-phrase is capitalized. A sub-phrase starts with `:`, `.`, `;`, `?`, `!`, or a dash (`-`, `–`, `‒`, `—`, or `―`) followed by a space.
    - Input: `Starting Sub-Phrase With a Small Word: a Trick, Perhaps?`
    - Output: `Starting Sub-Phrase With a Small Word: A Trick, Perhaps?`
