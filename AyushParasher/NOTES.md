# Notes

## Licence

The MIT License (MIT)

## Rules `titlecase()` applies

Rules run in this order. A word handled by an earlier rule is left alone by the later per-word rules.

1. By default, the text is split on runs of newlines, so a blank line is dropped. The processed lines are joined with `\n`.

   Input: `Line number one` + a blank line + `and Line three` + a trailing newline

   Output: `Line Number One\nAnd Line Three\n`

2. With `preserve_blank_lines=True`, the text is split on every newline, so blank lines stay.

   Input: `Line number one` + a blank line + `and Line three` + a trailing newline

   Output: `Line Number One\n\nAnd Line Three\n`

3. Each line is split into words on whitespace, and the original space characters are put back between those words.

   Input: `text\twith\ttabs`

   Output: `Text\tWith\tTabs`

4. With `normalise_space_characters=True`, the words are joined with one ordinary space.

   Input: `text\twith\ttabs`

   Output: `Text With Tabs`

5. When `callback` returns a non-empty string for a word, that string is the result for the word. The later start-of-line and end-of-line small-word capitalization leaves it unchanged.

   Input: `and then`, with a callback that returns `and` for that first word

   Output: `and Then`

6. When the whole line is uppercase, a word of dotted initials (`A.`, `A.B`, or `A.B.`) is kept as written.

   Input: `THE V. CASE`

   Output: `The V. Case`

7. A word that starts with `d` or `l`, an apostrophe (`'` or `‘`), then letters (optionally ending in `'s`) is rewritten at two characters only: the leading `d` or `l` is lowercased, and the letter after the apostrophe is capitalized.

   Input: `l'grange`

   Output: `l'Grange`

8. A word in that same apostrophe shape that starts with `o` is rewritten at two characters only: the leading `o` is capitalized, and the letter after the apostrophe is capitalized.

   Input: `o'clock`

   Output: `O'Clock`

9. A word that starts with `Mc`, `mc`, or `MC`, followed by at least two more word characters, is rewritten as `Mc` plus the titlecased remainder.

   Input: `mcdonald`

   Output: `McDonald`

10. The words `mr`, `mrs`, `ms`, and `dr` (any capitalization) get an uppercase first letter. The remaining letters stay as they were.

    Input: `mrs doubtfire`

    Output: `Mrs Doubtfire`

11. A word that contains a letter, a period, and another letter is left unchanged.

    Input: `this is just an example.com`

    Output: `This Is Just an example.com`

12. When the line is not entirely uppercase, a word that already contains an uppercase letter after its opening letters is left unchanged.

    Input: `iTunes should be unmolested`

    Output: `iTunes Should Be Unmolested`

13. A small word is lowercased. The small words are `a`, `an`, `and`, `as`, `at`, `but`, `by`, `en`, `for`, `if`, `in`, `of`, `on`, `or`, `the`, `to`, `v`, `v.`, `via`, `vs`, and `vs.`

    Input: `this v that`

    Output: `This v That`

14. A word that contains `/` and does not contain `//` is split on each `/`. Each piece is titlecased on its own, without the start-of-line and end-of-line small-word capitalization, and the pieces are joined again with `/`.

    Input: `a title and/or string`

    Output: `A Title and/or String`

15. A word that contains `//` stays one word. Later rules still apply, so an ordinary word of this shape only has its first letter capitalized.

    Input: `foo//bar`

    Output: `Foo//bar`

16. A word that contains `-` is split on each `-`. Each piece is titlecased on its own, without the start-of-line and end-of-line small-word capitalization, and the pieces are joined again with `-`.

    Input: `end-to-end`

    Output: `End-to-End`

17. When the whole line is uppercase, a word that is still being processed is lowercased before the acronym and first-letter rules.

    Input: `THIS IS ALL CAPS AND SHOULD BE ADDRESSED`

    Output: `This Is All Caps and Should Be Addressed`

18. A word of more than two letters made only of consonants is uppercased. For this test, `a`, `e`, `i`, `o`, `u`, and `y` count as vowels.

    Input: `cnn report`

    Output: `CNN Report`

19. Any other word has its first letter capitalized. Leading punctuation is skipped, and the rest of the word stays as it is.

    Input: `(hello world)`

    Output: `(Hello World)`

20. With `small_first_last=True` (the default), a small word at the start of the line is capitalized, including when punctuation comes before it. A word supplied by `callback` is skipped. `small_first_last=False` leaves that leading small word lowercased.

    Input: `'by the way'`

    Output: `'By the Way'`

21. With `small_first_last=True`, a small word at the end of the line is capitalized, including when punctuation follows it. A word supplied by `callback` is skipped. `small_first_last=False` leaves that trailing small word lowercased.

    Input: `nothing to be afraid of`

    Output: `Nothing to Be Afraid Of`

22. After the line is joined, a small word that follows `:` `.` `;` `?` `!` or a dash (`-`, `–`, `‒`, `—`, `―`) and a space is capitalized.

    Input: `jobs: the interview`

    Output: `Jobs: The Interview`

Repository:
https://github.com/ppannuto/python-titlecase

Git Commit SHA:
42f43e2de55bf003b286c6f8e8d8b2d26676a167

Commit Date:
2024-04-05T22:03:59-07:00

