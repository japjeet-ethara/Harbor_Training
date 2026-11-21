# python-titlecase notes

- Repository: https://github.com/ppannuto/python-titlecase
- Commit: `42f43e2de55bf003b286c6f8e8d8b2d26676a167`
- Commit date: 2024-04-05T22:03:59-07:00
- Source read: `titlecase/__init__.py` (version 2.4.1) and `LICENSE.txt`

## 1. Licence

The MIT License (MIT). Copyright (c) 2021 Patrick William Pannuto.

The module docstring also points at http://www.opensource.org/licenses/mit-license.php.

## 2. Rules `titlecase()` applies

Each example below was produced by calling `titlecase()` in this checkout. Inputs and outputs are shown as Python string literals so spaces and newlines stay visible.

1. **Small words stay lowercase in the middle of a title.** The small-word list is the New York Times list plus `v`, `v.`, `via`, `vs`, and `vs.`: `a`, `an`, `and`, `as`, `at`, `but`, `by`, `en`, `for`, `if`, `in`, `of`, `on`, `or`, `the`, `to`, `v`, `v.`, `via`, `vs`, `vs.`.
   - Input: `'the lord of the rings'`
   - Output: `'The Lord of the Rings'`

2. **A small word that is the first or the last word of a line is capitalized** (`small_first_last=True`, the default). Leading punctuation does not block this.
   - Input: `'a thing of'`
   - Output: `'A Thing Of'`
   - Input: `"'by the Way, small word at the start but within quotes.'"`
   - Output: `"'By the Way, Small Word at the Start but Within Quotes.'"`

3. **`v`, `v.`, `vs`, and `vs.` are small words**, so they stay lowercase in the middle.
   - Input: `'this vs. that'`
   - Output: `'This vs. That'`

4. **After a sub-phrase break, the next small word is capitalized.** The break is a colon, semicolon, period, question mark, exclamation mark, or dash (`-`, `–`, `‒`, `—`, `―`) followed by a space.
   - Input: `'Starting Sub-Phrase With a Small Word: a Trick, Perhaps?'`
   - Output: `'Starting Sub-Phrase With a Small Word: A Trick, Perhaps?'`

5. **A line that is entirely uppercase is lowercased first, then title-cased.** Small words still follow the rules above.
   - Input: `'THIS IS ALL CAPS AND SHOULD BE ADDRESSED'`
   - Output: `'This Is All Caps and Should Be Addressed'`

6. **On an all-uppercase line, initialisms made of capital letters and periods are left unchanged** (for example `A.B`, `A.B.`, `D.C.`). A run of capitals with no periods is not treated as initials.
   - Input: `'WASHINGTON, D.C. SHOULD BE FIXED BUT MIGHT BE A PROBLEM'`
   - Output: `'Washington, D.C. Should Be Fixed but Might Be a Problem'`

7. **A word that already contains an uppercase letter later in the word is left unchanged**, but only when the whole line is not all caps. This keeps names like `iTunes`, `AT&T`, and `Q&A`.
   - Input: `'iTunes should be unmolested'`
   - Output: `'iTunes Should Be Unmolested'`

8. **A word with a letter, a period, and another letter inside it is left unchanged.** That covers domains and URLs. A URL also contains `//`, which stops the slash-splitting rule below.
   - Input: `'this is http://foo.com'`
   - Output: `'This Is http://foo.com'`

9. **Words that start with `d`, `o`, or `l` plus `'` or `‘` get the letter after the apostrophe capitalized.** If the first letter is a vowel (`o`), it is capitalized too. If it is `d` or `l`, it stays lowercase. The rest of the word is kept as written.
   - Input: `"o'grange"`
   - Output: `"O'Grange"`
   - Input: `"l'grange"`
   - Output: `"l'Grange"`

10. **A word starting with `Mc` or `MC` is rewritten as `Mc` plus the title-cased remainder.**
    - Input: `'mccarthy'`
    - Output: `'McCarthy'`

11. **`Mr`, `Mrs`, `Ms`, and `Dr` keep the remainder of the word and only force the first letter to uppercase.** `Mss` does not match, so the all-consonant rule turns it into `MSS`.
    - Input: `'mr smith and dr jones'`
    - Output: `'Mr Smith and Dr Jones'`

12. **A word containing `/` but not `//` is split, and each piece is title-cased on its own.** Small words inside a piece stay small, because the first-and-last rule is turned off for those pieces.
    - Input: `'a title and/or string'`
    - Output: `'A Title and/or String'`

13. **A hyphenated word is split on `-`, and each piece is title-cased on its own**, again with the first-and-last rule off, so a small word in the middle of a compound stays small and the last piece is still capitalized when it is not small.
    - Input: `'end-to-end'`
    - Output: `'End-to-End'`

14. **A word of more than two letters that is made only of consonants is uppercased as an acronym.** `a`, `e`, `i`, `o`, `u`, and `y` count as vowels, so they stop this rule. Two letters or fewer (`st`) are ordinary words, not acronyms.
    - Input: `'words with all consonants like cnn'`
    - Output: `'Words With All Consonants Like CNN'`
    - Input: `'foo bar 5th st'`
    - Output: `'Foo Bar 5th St'`

15. **Any other word is capitalized at its first letter.** Leading punctuation stays in place, and a word that starts with a digit is left as it is.
    - Input: `'34th 3rd 2nd'`
    - Output: `'34th 3rd 2nd'`

16. **Each line is handled separately and joined back with `\n`.** A newline inside the input is kept.
    - Input: `"this shouldn't\nget mangled"`
    - Output: `"This Shouldn't\nGet Mangled"`

17. **Blank lines are collapsed by default.** Consecutive CR/LF breaks become one break. `preserve_blank_lines=True` keeps every empty line.
    - Input: `'Line number one\n\nand Line three\n'`
    - Output: `'Line Number One\nAnd Line Three\n'`
    - Same input with `preserve_blank_lines=True`: `'Line Number One\n\nAnd Line Three\n'`

18. **The original space characters between words are kept**, including tabs and other Unicode spaces. `normalise_space_characters=True` replaces them with a single normal space.
    - Input: `'text\twith\ttabs'`
    - Output: `'Text\tWith\tTabs'`
    - Same input with `normalise_space_characters=True`: `'Text With Tabs'`

19. **A callback may replace one word.** If it returns a non-empty string, that string is kept exactly and is not changed again by the first-word or last-word rule. This is how an abbreviation list forces a spelling such as `UDP` (which is not all consonants, because of `u`).
    - Input: `'a simple tcp and udp wrapper'` with no callback
    - Output: `'A Simple TCP and Udp Wrapper'`
    - Same input with a callback that returns `TCP` and `UDP` in uppercase
    - Output: `'A Simple TCP and UDP Wrapper'`
