# python-titlecase — reading notes

Sources: `titlecase/__init__.py` and `LICENSE.txt`.

## Repository Information

- Repository: https://github.com/ppannuto/python-titlecase
- Commit SHA: 42f43e2de55bf003b286c6f8e8d8b2d26676a167
- Commit Date: 2024-04-05T22:03:59-07:00

## 1. License

**The MIT License (MIT)** — Copyright (c) 2021 Patrick William Pannuto.

The module docstring also points to the MIT license
(<http://www.opensource.org/licenses/mit-license.php>).

## 2. Rules applied by `titlecase()`

`titlecase()` splits the input into lines, then into words and whitespace, and
processes each word through the following rules in order. Later line-level
steps then adjust small words at the edges of a line and after sub-sentence
punctuation.

1. **Split into lines, and optionally keep blank lines.**
   By default the text is split on runs of newlines (`[\r\n]+`), so blank
   lines are dropped. With `preserve_blank_lines=True` it is split on each
   individual newline (`[\r\n]`), so empty lines survive.
   - Input: `"one\n\nTwo"` → Output: `"One\nTwo"`
   - With `preserve_blank_lines=True`: `"One\n\nTwo"`

2. **Callback override.** If a `callback` is supplied and returns a truthy
   replacement for a word, that replacement is used verbatim and marked
   immutable, so later rules (including the first/last small-word rules) do
   not touch it. Returning `None` lets normal processing continue.
   - Callback that returns `word.upper()` for `tcp`/`udp`.
   - Input: `"a simple tcp and udp wrapper"` → Output: `"A Simple TCP and UDP Wrapper"`

3. **Keep all-caps initials.** On a line that is entirely uppercase, a word
   matching the initials pattern (e.g. `A.B.C`, `A.B`) is left exactly as-is.
   - Input: `"A.B.C IS HERE"` → Output: `"A.B.C Is Here"`

4. **Apostrophe-second words** (`o'reilly`, `d'artagnan`, etc.). The letter
   after the apostrophe is uppercased. If the first character is a single
   consonant (anything other than `a e i o u`), it is lowercased; if it is a
   vowel it is uppercased.
   - Input: `"o'reilly and d'artagnan"` → Output: `"O'Reilly and D'Artagnan"`

5. **Mc/Mac-style prefixes.** A word starting with `mc`/`Mc`/`MC` has the
   prefix normalized with `capitalize()` (becoming `Mc`) and the remainder is
   recursively title-cased.
   - Input: `"ronald mcdonald"` → Output: `"Ronald McDonald"`

6. **Titles Mr/Mrs/Ms/Dr.** A word that is exactly `mr`, `mrs`, `ms`, or `dr`
   (case-insensitive, no trailing period) is capitalized only in its first
   letter, so e.g. `MRS` does not become the consonant acronym `MRS`.
   - Input: `"MRS SMITH"` → Output: `"Mrs Smith"`

7. **Inline periods.** A word containing `letter.letter` (an abbreviation or
   a domain-like token, such as `U.S.` or `example.com`) is left unchanged.
   - Input: `"visit example.com now"` → Output: `"Visit example.com Now"`

8. **Embedded capitals (camelCase).** On a line that is not all uppercase, a
   word with a lowercase letter followed later by an uppercase letter (e.g.
   `fooBar`, `iPhone`) is left unchanged.
   - Input: `"the fooBar test"` → Output: `"The fooBar Test"`

9. **Small words are lowercased.** A word matching the small-word list exactly
   is lowercased. The list is: `a, an, and, as, at, but, by, en, for, if, in,
   of, on, or, the, to, v, v., via, vs, vs.` (from the New York Times Manual
   of Style, plus `v`/`vs`).
   - Input: `"war and peace"` → Output: `"War and Peace"`

10. **Slash-separated parts.** If a word contains `/` but not `//`, each part
    is recursively title-cased separately and re-joined with `/`.
    - Input: `"foo/bar"` → Output: `"Foo/Bar"`

11. **Hyphenated words.** If a word contains `-`, each part is recursively
    title-cased separately and re-joined with `-`. Recursion disables the
    first/last small-word rule.
    - Input: `"mother-in-law"` → Output: `"Mother-in-Law"`

12. **Lowercase all-caps words.** On an all-uppercase line, any word not
    already handled above is lowercased before the remaining rules run.
    - Input: `"THIS IS A TEST"` → Output: `"This Is a Test"`

13. **Consonant-only acronyms.** A word of more than two characters made
    entirely of consonants (vowels `a e i o u`, and also `y`, are excluded)
    is uppercased as an acronym.
    - Input: `"the xkcd comic"` → Output: `"The XKCD Comic"`

14. **Default capitalization.** Any remaining word has its first letter
    capitalized, preserving any leading punctuation.
    - Input: `"hello world"` → Output: `"Hello World"`

15. **Small words at the start and end of a line.** Unless
    `small_first_last=False`, a small word at the beginning or at the end of a
    line is capitalized. Words marked immutable by a callback are skipped.
    - Input: `"the end of the line for"` → Output: `"The End of the Line For"`

16. **Small words after sub-sentence punctuation.** A small word immediately
    after `:`, `;`, `.`, `?`, `!`, or a dash followed by a space is
    capitalized.
    - Input: `"the lord of the rings: the fellowship"` → Output: `"The Lord of the Rings: The Fellowship"`

17. **Reassemble the line.** Words are re-joined with their original
    whitespace, so spacing and tabs are preserved by default. With
    `normalise_space_characters=True`, all inter-word whitespace becomes a
    single normal space. Processed lines are finally joined with `\n`.
    - Input: `"a\tb"` → Output: `"A\tB"`
    - With `normalise_space_characters=True`: `"A B"`
