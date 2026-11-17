# Titlecase notes

- Repository URL: https://github.com/ppannuto/python-titlecase
- Commit SHA: 42f43e2de55bf003b286c6f8e8d8b2d26676a167
- Commit date: 2024-04-05 22:03:59 -07:00

## Licence

The licence name is the **MIT License** (the file heading is `The MIT License (MIT)`).

## Rules applied by `titlecase()`

Rules run in this order. Each word is handled by the first matching word rule; the line rules run after the words are decided.

The small words are: a, an, and, as, at, but, by, en, for, if, in, of, on, or, the, to, v, v., via, vs, vs. That list comes from the New York Times Manual of Style, plus `v` and `vs`.

1. **Each line is title-cased on its own, then the lines are joined with `\n`.**
   - Input: `this shouldn't\nget mangled`
   - Output: `This Shouldn't\nGet Mangled`

2. **A line is split on whitespace, and that whitespace is kept.**
   - Input: `text\twith\ttabs`
   - Output: `Text\tWith\tTabs`

3. **A callback can replace a word. A non-empty result is kept as-is, including later first-word and last-word capitalization.**
   - Input: `a cat` with a callback that returns `a` for that word
   - Output: `a Cat`

4. **On a fully uppercase line, a word made only of uppercase initials and periods is left unchanged.** Patterns such as `A.` and `A.B` match.
   - Input: `WASHINGTON, D.C. IS NEXT`
   - Output: `Washington, D.C. Is Next`

5. **A word matching `d'…`, `o'…`, or `l'…` (straight or curly apostrophe, optional trailing `'s`) is recased.** If the first letter is a consonant (`d` or `l`), it stays lowercase and the letter after the apostrophe is capitalized. If the first letter is a vowel (`o`), both of those letters are capitalized. Any characters after that keep their existing case.
   - Input: `l'grange`
   - Output: `l'Grange`

6. **A word starting with `Mc`, `mc`, or `MC`, followed by at least two more characters, becomes `Mc` plus the title-cased remainder.** `Mac` is not a special prefix. A bare `Mc` is too short for this rule.
   - Input: `mcdonald`
   - Output: `McDonald`

7. **`Mr`, `Mrs`, `Ms`, and `Dr` (any capitalization) capitalize only the first character. The rest of the word stays as written.**
   - Input: `mr smith`
   - Output: `Mr Smith`

8. **A word that contains `letter.letter` is left unchanged.** This keeps domains, dotted initials, and similar tokens.
   - Input: `this is just an example.com`
   - Output: `This Is Just an example.com`

9. **On a line that is not fully uppercase, a word that already contains an uppercase letter after another letter is left unchanged.**
   - Input: `iTunes should be unmolested`
   - Output: `iTunes Should Be Unmolested`

10. **A word that is exactly a small word is lowercased.**
    - Input: `the lord of the rings`
    - Output: `The Lord of the Rings`

11. **A word that contains `/` but not `//` is split on `/`, and each piece is title-cased with first-word and last-word small-word capitalization turned off. The pieces are joined back with `/`.** A word containing `//` is not split.
    - Input: `a title and/or string`
    - Output: `A Title and/or String`

12. **A word that contains `-` is split on `-`, and each piece is title-cased with first-word and last-word small-word capitalization turned off. The pieces are joined back with `-`.**
    - Input: `end-to-end`
    - Output: `End-to-End`

13. **If the whole line is uppercase, the current word is lowercased before the remaining word rules.** Initials and other words already kept above are not lowercased.
    - Input: `THIS IS ALL CAPS`
    - Output: `This Is All Caps`

14. **A word of only consonants, longer than two letters, is uppercased as an acronym.** `a`, `e`, `i`, `o`, `u`, and `y` count as vowels, so they block this rule. A short consonant word such as `st` is not treated as an acronym.
    - Input: `words like cnn`
    - Output: `Words Like CNN`

15. **Any other word capitalizes its first letter and leaves the rest unchanged.** Leading punctuation stays in place. A token with no leading letter, such as `34th`, is unchanged.
    - Input: `hello world`
    - Output: `Hello World`

16. **With `small_first_last` left at its default (`True`), a small word at the start of the line is capitalized.** Leading punctuation can sit in front of that word. A word locked by a callback is skipped.
    - Input: `a thing`
    - Output: `A Thing`

17. **With `small_first_last` left at its default, a small word at the end of the line is capitalized.** One trailing punctuation character can follow it. A word locked by a callback is skipped.
    - Input: `nothing to be afraid of`
    - Output: `Nothing to Be Afraid Of`

18. **With `normalise_space_characters=True`, the original whitespace between words is replaced by a single normal space.** The default is to keep the original whitespace (rule 2).
    - Input: `text\twith\ttabs`
    - Output: `Text With Tabs`

19. **A small word that follows sub-phrase punctuation and a space is capitalized.** The punctuation is `:`, `.`, `;`, `?`, `!`, or a hyphen or dash (`-`, `–`, `‒`, `—`, `―`).
    - Input: `a trick: a start`
    - Output: `A Trick: A Start`

20. **Blank lines are removed unless `preserve_blank_lines=True`.** The default splits on one or more line breaks, so consecutive breaks collapse. With the flag set, each break is kept.
    - Input: `Line number one\n\nand Line three\n`
    - Output (default): `Line Number One\nAnd Line Three\n`
    - Output (`preserve_blank_lines=True`): `Line Number One\n\nAnd Line Three\n`
