# Titlecase notes

## Licence

The MIT License (MIT)

## Source

Repository URL:
https://github.com/ppannuto/python-titlecase

Original Git commit SHA:
42f43e2de55bf003b286c6f8e8d8b2d26676a167

Commit date:
2024-04-05T22:03:59-07:00

## Rules applied by `titlecase`

`titlecase` walks the text line by line, then word by word, and applies the rules below in this order. The small-word list is the New York Times Manual of Style list plus `v`, `v.`, `vs`, and `vs.`: a, an, and, as, at, but, by, en, for, if, in, of, on, or, the, to, v, v., via, vs, vs.

1. The text is split on runs of `\r` and `\n`, so consecutive breaks collapse and blank lines drop out. The finished lines are joined with `\n`.
   - Input: `Line number one\n\nand Line three\n`
   - Output: `Line Number One\nAnd Line Three\n`

2. With `preserve_blank_lines=True`, the text is split on every single line break, and empty lines stay in the output.
   - Input: `Line number one\n\nand Line three\n`
   - Output: `Line Number One\n\nAnd Line Three\n`

3. Each line is split into words on whitespace. By default the original whitespace is put back between those words, including tabs and non-breaking spaces.
   - Input: `text\twith\ttabs`
   - Output: `Text\tWith\tTabs`

4. With `normalise_space_characters=True`, the words of a line are joined with one ordinary space.
   - Input: `text\twith\ttabs`
   - Output: `Text With Tabs`

5. A line that is already equal to its uppercase form is an all-caps line. A word on that line which is still unmatched after the special cases below is lowercased before acronym detection and ordinary capitalization.
   - Input: `THIS IS ALL CAPS AND SHOULD BE ADDRESSED`
   - Output: `This Is All Caps and Should Be Addressed`

6. When a `callback(word, all_caps=...)` returns a non-empty string, that string becomes the word and the later per-word rules leave it alone. A false return (such as `None` or `""`) means titlecasing continues.
   - Input: `a simple tcp and udp wrapper`, with a callback that returns `TCP` for `tcp` and `UDP` for `udp`
   - Output: `A Simple TCP and UDP Wrapper`

7. A callback result is marked immutable, so the first-word and last-word small-word capitalization in rules 20 and 21 leaves it as the callback wrote it.
   - Input: `the great gatsby`, with a callback that returns `the` for that word
   - Output: `the Great Gatsby`

8. On an all-caps line, a word that is a sequence of uppercase initials (`A.`, `A.B`, `A.B.`, `D.C.`, and the same shapes repeated) is kept character for character. This runs before the small-word rule, so an initial such as `V.` stays uppercase.
   - Input: `THIS V. THAT`
   - Output: `This V. That`

9. A word matching `d'…`, `o'…`, or `l'…` (straight or curly apostrophe, with an optional `'s` ending) is recased only at the first letter and the letter after the apostrophe. The rest of the spelling stays as it was (`O'GranGe` stays `O'GranGe`). When the first letter is a vowel, that letter is capitalized.
   - Input: `my name is o'reilly`
   - Output: `My Name Is O'Reilly`

10. In that same apostrophe form, a consonant first letter (`d` or `l`) is written in lowercase, and the letter after the apostrophe is capitalized.
    - Input: `l'grange`
    - Output: `l'Grange`

11. A word that starts with `Mc`, `mc`, or `MC` and has at least two more word characters is written as `Mc` followed by the titlecased remainder.
    - Input: `mcdonald`
    - Output: `McDonald`

12. `Mr`, `Mrs`, `Ms`, and `Dr` (any capitalization) keep every character after the first, and the first character is forced to uppercase. On an all-caps line the remaining capitals stay capitals.
    - Input: `MRS DOUBTFIRE`
    - Output: `MRS Doubtfire`

13. A word that contains a letter, a period, and another letter (`example.com`, `i.e.`, `Ph.D`, `D.C.`) is kept unchanged.
    - Input: `this is just an example.com`
    - Output: `This Is Just an example.com`

14. On a line that is not all caps, a word that contains an uppercase letter after other letters (`iTunes`, `AT&T`, `Q&A`) is kept unchanged.
    - Input: `iTunes should be unmolested`
    - Output: `iTunes Should Be Unmolested`

15. A word that is one of the small words listed above is written in lowercase.
    - Input: `this vs. that`
    - Output: `This vs. That`

16. A word that contains `/` and does not contain `//` is split on each `/`. Each piece is titlecased with `small_first_last` turned off, then the pieces are joined with `/` again.
    - Input: `a title and/or string`
    - Output: `A Title and/or String`

17. A word that contains `//` stays a single word, and the other word rules then apply to it as a whole.
    - Input: `go to http://example`
    - Output: `Go to Http://example`

18. A word that contains `-` is split on each hyphen. Each piece is titlecased with `small_first_last` turned off, then the pieces are joined with `-` again. A small word in the middle of the compound stays lowercase.
    - Input: `out-of-date`
    - Output: `Out-of-Date`

19. A word of more than two letters made only of consonants is written in full uppercase as an acronym. For this test, a, e, i, o, u, and y are vowels.
    - Input: `html guide`
    - Output: `HTML Guide`

20. A consonant-only word of two letters or fewer is capitalized as an ordinary word. `St` is the case the implementation calls out.
    - Input: `foo bar 5th st`
    - Output: `Foo Bar 5th St`

21. Any remaining word is capitalized by uppercasing its first letter. Leading punctuation stays in front of that letter, and the rest of the word, including digits and trailing punctuation, stays as it was.
    - Input: `(hello world)`
    - Output: `(Hello World)`

22. When `small_first_last` is true (the default), a small word at the start of the line is capitalized. Punctuation before that word stays in place. Words marked immutable by a callback are left alone. Slash and hyphen pieces are processed with this step turned off; it still runs on the finished token when that token is the first word of the line (`and/or` on its own becomes `And/Or`).
    - Input: `'by the Way'`
    - Output: `'By the Way'`

23. When `small_first_last` is true, a small word at the end of the line is capitalized, including one optional trailing punctuation character. Immutable callback results are left alone. The same end-of-line pass capitalizes a final small piece of a hyphenated or slashed token (`five-and` becomes `Five-And`).
    - Input: `"Nothing to Be Afraid of?"`
    - Output: `"Nothing to Be Afraid Of?"`

24. After the line is assembled, a small word that begins a sub-phrase is capitalized. A sub-phrase is a colon, period, semicolon, question mark, exclamation mark, or dash (`-`, `–`, `‒`, `—`, `―`) followed by a space. A comma does not start a sub-phrase (`one, the man` stays `One, the Man`).
    - Input: `Starting Sub-Phrase With a Small Word: a Trick, Perhaps?`
    - Output: `Starting Sub-Phrase With a Small Word: A Trick, Perhaps?`
