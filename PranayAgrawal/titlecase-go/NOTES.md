# Titlecase notes

## Licence

The MIT License (MIT)

## Rules the `titlecase` function applies

Small words, kept in lowercase unless a later rule capitalizes them, are: a, an, and, as, at, but, by, en, for, if, in, of, on, or, the, to, v, v., via, vs, vs. That list follows the New York Times Manual of Style, plus v and vs.

1. Consecutive line breaks collapse into one, so a blank line is dropped. Processed lines are joined with `\n`.
   - Input: `Line number one\n\nand Line three\n`
   - Output: `Line Number One\nAnd Line Three\n`

2. With `preserve_blank_lines=True`, each line break is kept, including blank lines.
   - Input: `Line number one\n\nand Line three\n`
   - Output: `Line Number One\n\nAnd Line Three\n`

3. Whitespace between words is preserved, including tabs and other space characters.
   - Input: `text\twith\ttabs`
   - Output: `Text\tWith\tTabs`

4. With `normalise_space_characters=True`, every run of whitespace between words becomes a single normal space.
   - Input: `text\twith\ttabs`
   - Output: `Text With Tabs`

5. If `callback` returns a non-empty string for a word, that string is used as the word. Later rules, including first-and-last small-word capitalization, leave it unchanged.
   - Input: `a simple tcp and udp wrapper`, with a callback that returns `TCP` and `UDP`
   - Output: `A Simple TCP and UDP Wrapper`

6. On a fully uppercase line, an initials token such as `A.B` or `D.C.` is left unchanged.
   - Input: `WASHINGTON, D.C. SHOULD BE FIXED BUT MIGHT BE A PROBLEM`
   - Output: `Washington, D.C. Should Be Fixed but Might Be a Problem`

7. A word that starts with `d`, `o`, or `l` and an apostrophe (`'` or `‘`), optionally ending in `'s`, capitalizes the letter after the apostrophe. A leading consonant (`d` or `l`) is lowercased. A leading vowel (`o`) is capitalized. The rest of the word stays as written.
   - Input: `l'grange`
   - Output: `l'Grange`

8. A word starting with `Mc`, `mc`, or `MC`, followed by at least two word characters, is written as `Mc` plus the titlecased remainder.
   - Input: `mcclelland`
   - Output: `McClelland`

9. `Mr`, `Mrs`, `Ms`, and `Dr` (any capitalization) keep their remaining letters and capitalize only the first letter.
   - Input: `dr`
   - Output: `Dr`

10. A word that contains a letter, a period, and another letter is left unchanged. This covers names like `example.com` and `del.icio.us`.
    - Input: `example.com`
    - Output: `example.com`

11. If the line is not fully uppercase, a word that already contains a capital letter after its opening letters is left unchanged.
    - Input: `iTunes`
    - Output: `iTunes`

12. A small word is lowercased.
    - Input: `this v that`
    - Output: `This v That`

13. A word that contains `/` but not `//` is split on `/`. Each piece is titlecased on its own, with first-and-last small-word capitalization turned off, then joined again with `/`. A `//`, as in a URL, is not split.
    - Input: `word/word`
    - Output: `Word/Word`

14. A word that contains `-` is split on `-`. Each piece is titlecased on its own, with first-and-last small-word capitalization turned off, then joined again with `-`.
    - Input: `end-to-end`
    - Output: `End-to-End`

15. On a fully uppercase line, a word that is still being processed is lowercased before it is capitalized, so the line is not left in all capitals.
    - Input: `THIS IS ALL CAPS AND SHOULD BE ADDRESSED`
    - Output: `This Is All Caps and Should Be Addressed`

16. A word made only of consonants, longer than two letters, is treated as an acronym and uppercased. `a`, `e`, `i`, `o`, `u`, and `y` count as vowels, so a short word such as `St` is capitalized as a normal word.
    - Input: `cnn`
    - Output: `CNN`

17. Any other word has its first letter capitalized. Leading punctuation stays in front of that letter, and the rest of the word is unchanged. A word with no letter, such as an ordinal, stays as written.
    - Input: `yea no`
    - Output: `Yea No`

18. With `small_first_last` left on (the default), a small word at the start of the line is capitalized, including when punctuation stands in front of it. A small word at the end is capitalized, including optional trailing punctuation. A word fixed by the callback is skipped. Slash and hyphen pieces are processed with this rule turned off, so a small word in the middle of those pieces stays lowercase.
    - Input: `Small word at end is nothing to be afraid of`
    - Output: `Small Word at End Is Nothing to Be Afraid Of`

19. After the line is assembled, a small word that follows `:`, `.`, `;`, `?`, `!`, or a dash (`-`, `–`, `‒`, `—`, `―`) and a space is capitalized.
    - Input: `Starting Sub-Phrase With a Small Word: a Trick, Perhaps?`
    - Output: `Starting Sub-Phrase With a Small Word: A Trick, Perhaps?`
