# Titlecase notes

## Licence

The MIT License (MIT)

## Rules applied by `titlecase`

Small words, left lowercase except where a later rule capitalizes them, are: a, an, and, as, at, but, by, en, for, if, in, of, on, or, the, to, v, v., via, vs, vs.

1. **Lines are split on line breaks.** Consecutive breaks are collapsed, so a blank line is dropped. With `preserve_blank_lines=True`, each break is kept and blank lines remain. Lines are joined back with `\n`.
   - Input: `Line number one\n\nand Line three\n`
   - Output: `Line Number One\nAnd Line Three\n`
   - With `preserve_blank_lines=True`, that same input stays as `Line Number One\n\nAnd Line Three\n`.

2. **A callback can replace a word.** If `callback(word, all_caps=...)` returns a non-empty string, that string is used for the word. The replacement is then left unchanged by the first-word and last-word small-word capitalization.
   - Input: `a simple tcp and udp wrapper` with a callback that returns `UDP` for `udp`
   - Output: `A Simple TCP and UDP Wrapper`

3. **Dotted initials on an all-caps line are kept.** When every character of the line is already uppercase, a word of initials such as `A.B` or `D.C.` is copied through unchanged.
   - Input: `WASHINGTON, D.C. SHOULD BE FIXED`
   - Output: `Washington, D.C. Should Be Fixed`

4. **`d'`, `o'`, and `l'` forms are recapitalized around the apostrophe.** The letter after `'` or `‘` is capitalized. A vowel before the apostrophe is capitalized; a consonant before it is lowercased. Any characters after that letter are kept as they were.
   - Input: `my name is o'reilly`
   - Output: `My Name Is O'Reilly`

5. **An `Mc` prefix is capitalized and the remainder is titlecased.** This matches a word that begins with `Mc`, `mc`, or `MC` and has at least two further characters.
   - Input: `mcclelland`
   - Output: `McClelland`

6. **`Mr`, `Mrs`, `Ms`, and `Dr` keep the rest of the word and capitalize only the first letter.**
   - Input: `mr mrs ms dr`
   - Output: `Mr Mrs Ms Dr`

7. **A word with an internal period, or with a capital later in the word, is left as written.** An internal period is a letter, a `.`, and another letter (`example.com`, `i.e.`). A later capital (`iTunes`, `AT&T`) is kept when the line is not entirely uppercase. A word that contains `//` is also left whole, so it is not split on `/`.
   - Input: `this is just an example.com`
   - Output: `This Is Just an example.com`

8. **Small words are lowercased.**
   - Input: `pride and prejudice`
   - Output: `Pride and Prejudice`

9. **A word that contains `/` and does not contain `//` is split on each `/`, and each piece is titlecased on its own.** Inside those pieces, a small word is not forced to a capital just because it is first or last in its piece.
   - Input: `word/word`
   - Output: `Word/Word`

10. **A hyphenated word is split on each `-`, and each piece is titlecased on its own.** The same first-and-last exception as the slash rule applies inside the pieces.
    - Input: `end-to-end`
    - Output: `End-to-End`

11. **On an all-caps line, a word that was not already handled is lowercased before the acronym and ordinary-word rules run.** The line then reads as title case.
    - Input: `THIS IS ALL CAPS`
    - Output: `This Is All Caps`

12. **A word of only consonants, longer than two letters, is treated as an acronym and uppercased.** `a`, `e`, `i`, `o`, `u`, and `y` count as vowels, so they block this rule. `St` stays title case because it is only two letters.
    - Input: `words like cnn are acronyms`
    - Output: `Words Like CNN Are Acronyms`

13. **Any other word has its first letter capitalized.** Leading punctuation stays in front of that letter, and the rest of the word is unchanged.
    - Input: `hello world`
    - Output: `Hello World`

14. **The first and last words of a line have a leading small word capitalized.** Punctuation before the first small word, or one punctuation mark after the last, stays in place. This runs when `small_first_last` is true, which is the default. Words supplied by the callback are skipped. Recursive titlecasing of slash and hyphen pieces turns this off.
    - Input: `Small word at end is nothing to be afraid of`
    - Output: `Small Word at End Is Nothing to Be Afraid Of`

15. **A small word after sub-phrase punctuation and a space is capitalized.** The punctuation is `:`, `.`, `;`, `?`, `!`, or a dash (`-`, `–`, `‒`, `—`, `―`).
    - Input: `Starting Sub-Phrase With a Small Word: a Trick, Perhaps?`
    - Output: `Starting Sub-Phrase With a Small Word: A Trick, Perhaps?`

16. **Spaces between words are preserved.** With `normalise_space_characters=True`, those spaces are replaced by a single ordinary space.
    - Input: `text\twith\ttabs`
    - Output: `Text\tWith\tTabs`
    - With `normalise_space_characters=True`, that same input becomes `Text With Tabs`.
