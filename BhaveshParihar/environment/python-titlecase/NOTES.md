# Titlecase notes

## Licence

The MIT License (MIT)

## Rules applied by `titlecase`

Small words, left in lowercase in the middle of a title, are: a, an, and, as, at, but, by, en, for, if, in, of, on, or, the, to, v, v., via, vs, vs.

1. A callback return value replaces that word, and later first-word and last-word fixes leave it unchanged.
   - Input: `a simple tcp and udp wrapper` with a callback that returns `TCP` and `UDP`
   - Output: `A Simple TCP and UDP Wrapper`

2. On a fully uppercase line, initials made of capital letters and periods stay as written.
   - Input: `WASHINGTON, D.C. SHOULD BE FIXED BUT MIGHT BE A PROBLEM`
   - Output: `Washington, D.C. Should Be Fixed but Might Be a Problem`

3. A word shaped like `d'…`, `l'…`, or `o'…` (straight or curly apostrophe, optional trailing `'s`) keeps a leading consonant lowercase and capitalizes a leading vowel, and capitalizes the letter after the apostrophe.
   - Input: `l'grange`
   - Output: `l'Grange`

4. A word that starts with `Mc`, `mc`, `Mac`, `mac`, or `MC` gets that prefix capitalized, and the remainder is titlecased.
   - Input: `mcclelland`
   - Output: `McClelland`

5. `Mr`, `Mrs`, `Ms`, and `Dr` keep the rest of their letters and capitalize only the first letter.
   - Input: `mr smith`
   - Output: `Mr Smith`

6. A word that contains a letter, a period, and a letter stays unchanged.
   - Input: `this is just an example.com`
   - Output: `This Is Just an example.com`

7. On a line that is not fully uppercase, a word that already has an internal capital stays unchanged.
   - Input: `iTunes should be unmolested`
   - Output: `iTunes Should Be Unmolested`

8. A small word in the middle of a line is lowercased.
   - Input: `this vs that`
   - Output: `This vs That`

9. A word with a single slash is titlecased on each side. A small word on either side stays lowercase.
   - Input: `a title and/or string`
   - Output: `A Title and/or String`

10. A word containing `//` stays one word, so a URL is left intact.
    - Input: `this is http://foo.com`
    - Output: `This Is http://foo.com`

11. A hyphenated word is titlecased on each side. A small word on either side stays lowercase.
    - Input: `end-to-end`
    - Output: `End-to-End`

12. On a fully uppercase line, remaining words are lowercased and then titlecased.
    - Input: `THIS IS ALL CAPS AND SHOULD BE ADDRESSED`
    - Output: `This Is All Caps and Should Be Addressed`

13. A word longer than two letters that contains only consonants (`y` counts as a vowel) is written in full capitals as an acronym. A shorter consonant-only word, such as `St`, is titlecased as an ordinary word.
    - Input: `Words with all consonants like cnn are acronyms`
    - Output: `Words With All Consonants Like CNN Are Acronyms`

14. Any other word capitalizes its first letter and leaves the remaining characters as they are.
    - Input: `yea no`
    - Output: `Yea No`

15. With the default `small_first_last=True`, a small word at the start of the line is capitalized, including when punctuation precedes it.
    - Input: `'by the Way, small word at the start but within quotes.'`
    - Output: `'By the Way, Small Word at the Start but Within Quotes.'`

16. With the default `small_first_last=True`, a small word at the end of the line is capitalized, including when punctuation follows it.
    - Input: `Small word at end is nothing to be afraid of`
    - Output: `Small Word at End Is Nothing to Be Afraid Of`

17. A small word is capitalized when it opens a sub-phrase after a colon, period, semicolon, question mark, exclamation mark, or dash and a space.
    - Input: `Starting Sub-Phrase With a Small Word: a Trick, Perhaps?`
    - Output: `Starting Sub-Phrase With a Small Word: A Trick, Perhaps?`

18. Consecutive line breaks are collapsed, so a blank line is removed. `preserve_blank_lines=True` keeps each blank line.
    - Input: `Line number one`, a blank line, then `and Line three`
    - Output: `Line Number One` followed immediately by `And Line Three`

19. The original space characters between words are kept. `normalise_space_characters=True` replaces them with ordinary spaces.
    - Input: `text`, a tab, `with`, a tab, `tabs`, with `normalise_space_characters=True`
    - Output: `Text With Tabs`
