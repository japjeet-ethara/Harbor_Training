# Repository Information

- Repository URL: [https://github.com/ppannuto/python-titlecase](https://github.com/ppannuto/python-titlecase)
- Commit SHA: 42f43e2de55bf003b286c6f8e8d8b2d26676a167
- Commit Date: 2024-04-05T22:03:59-07:00  
  
  
Titlecase notes

## Licence

The MIT License (MIT)

## Rules the `titlecase` function applies

The small-word list comes from the New York Times Manual of Style, plus `v` and `vs`: a, an, and, as, at, but, by, en, for, if, in, of, on, or, the, to, v, v., via, vs, vs.

1. Split the text into lines on newlines. By default, consecutive line breaks count as one break, so blank lines are dropped. Processed lines are joined back with `\n`.
   - Input: `Line number one\n\nand Line three\n`
   - Output: `Line Number One\nAnd Line Three\n`
2. With `preserve_blank_lines=True`, split on each newline and keep blank lines.
   - Input: `Line number one\n\nand Line three\n`
   - Output: `Line Number One\n\nAnd Line Three\n`
3. Keep the original whitespace between words. With `normalise_space_characters=True`, join the words with a single normal space instead.
   - Input: `text\twith\ttabs` (with `normalise_space_characters=True`)
   - Output: `Text With Tabs`
4. If a callback returns text for a word, use that text and do not change it later, including the first-word and last-word small-word capitalization.
   - Input: `the end` (callback returns `the` for `the`)
   - Output: `the End`
5. On a line that is entirely uppercase, leave a word of uppercase initials unchanged (`A.`, `A.B`, `D.C.`, and repeats of those forms).
   - Input: `WASHINGTON, D.C. SHOULD BE FIXED`
   - Output: `Washington, D.C. Should Be Fixed`
6. For a word that starts with `d`, `o`, or `l` and an apostrophe (`'` or `‘`), capitalize the letter after the apostrophe. Capitalize a vowel in the first position (`o` becomes `O`); lowercase a consonant there (`l` stays `l`). A trailing `'s` stays in place.
   - Input: `o'grange l'grange`
   - Output: `O'Grange l'Grange`
7. If a word starts with `Mc`, `mc`, or `MC` and at least two more characters follow, capitalize the prefix as `Mc` and titlecase the rest.
   - Input: `mcclelland`
   - Output: `McClelland`
8. For `Mr`, `Mrs`, `Ms`, and `Dr` in any case, uppercase only the first letter and leave the remaining letters as they were.
   - Input: `mr smith and dr jones`
   - Output: `Mr Smith and Dr Jones`
9. Leave a word unchanged when it contains an inline period between letters, as in a hostname or an abbreviation inside the word.
   - Input: `this is just an example.com`
   - Output: `This Is Just an example.com`
10. Leave a word unchanged when the line is not entirely uppercase and the word already contains a capital letter after another letter, as in mixed-case names and brands.
    - Input: `iTunes should be unmolested`
      - Output: `iTunes Should Be Unmolested`
11. Lowercase a small word (`a`, `an`, `and`, `as`, `at`, `but`, `by`, `en`, `for`, `if`, `in`, `of`, `on`, `or`, `the`, `to`, `v`, `v.`, `via`, `vs`, `vs.`).
    - Input: `this vs. that`
      - Output: `This vs. That`
12. If a word contains `/` and does not contain `//`, titlecase each slash-separated part on its own and rejoin them with `/`. Small words inside those parts stay lowercase.
    - Input: `word/word`
      - Output: `Word/Word`
13. If a word contains `-`, titlecase each hyphen-separated part on its own and rejoin them with `-`.
    - Input: `end-to-end`
      - Output: `End-to-End`
14. If the whole line is uppercase, lowercase each remaining word before the final capitalization rules, so an all-caps line is not left in all caps.
    - Input: `THIS IS ALL CAPS AND SHOULD BE ADDRESSED`
      - Output: `This Is All Caps and Should Be Addressed`
15. If a word is longer than two letters and every letter is a consonant (`a`, `e`, `i`, `o`, `u`, and `y` are not consonants), treat it as an acronym and uppercase it. A short word such as `St` is not treated this way.
    - Input: `words with all consonants like cnn`
      - Output: `Words With All Consonants Like CNN`
16. Otherwise, capitalize the first letter. Leading punctuation stays in front of that letter. A word that starts with a digit has no letter for this step to change, so `34th` stays `34th`.
    - Input: `hello world`
      - Output: `Hello World`
17. Capitalize a small word at the start of the line, including when punctuation comes before it. Skip this when a callback froze that word.
    - Input: `'by the Way, small word at the start but within quotes.'`
      - Output: `'By the Way, Small Word at the Start but Within Quotes.'`
18. Capitalize a small word at the end of the line, including when punctuation follows it. Skip this when a callback froze that word.
    - Input: `Small word at end is nothing to be afraid of`
      - Output: `Small Word at End Is Nothing to Be Afraid Of`
19. Capitalize a small word that opens a sub-phrase: the word right after `:`, `.`, `;`, `?`, `!`, or a dash (`-`, `–`, `‒`, `—`, `―`) followed by a space.
    - Input: `Starting Sub-Phrase With a Small Word: a Trick, Perhaps?`
      - Output: `Starting Sub-Phrase With a Small Word: A Trick, Perhaps?`
