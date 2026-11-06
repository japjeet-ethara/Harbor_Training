# python-titlecase

- Repository URL: https://github.com/ppannuto/python-titlecase
- Commit SHA: 42f43e2de55bf003b286c6f8e8d8b2d26676a167
- Commit date: 2024-04-05T22:03:59-07:00
- License: MIT

These rules describe the default behavior of `titlecase()` in `titlecase/__init__.py` at that commit, with the third-party `regex` package installed. Each input below was passed to that function. Where a string contains an escape, the input and output are Python literals.

## Behavior rules

1. A small word that is neither the first nor the last word of a line is lowercased. The small words are `a`, `an`, `and`, `as`, `at`, `but`, `by`, `en`, `for`, `if`, `in`, `of`, `on`, `or`, `the`, `to`, `v`, `v.`, `via`, `vs`, and `vs.`.

   Input: `life via the web`

   Output: `Life via the Web`

2. A small word at the beginning of a line is capitalized, and punctuation placed before it stays in place.

   Input: `'by the Way, small word at the start but within quotes.'`

   Output: `'By the Way, Small Word at the Start but Within Quotes.'`

3. A small word at the end of a line is capitalized, and punctuation placed after it stays in place.

   Input: `"Nothing to Be Afraid of?"`

   Output: `"Nothing to Be Afraid Of?"`

4. A small word is capitalized when it immediately follows a subphrase delimiter and a space. Those delimiters are `:`, `;`, `.`, `?`, `!`, and the dashes `-`, `–`, `‒`, `—`, and `―`.

   Input: `Starting Sub-Phrase With a Small Word: a Trick, Perhaps?`

   Output: `Starting Sub-Phrase With a Small Word: A Trick, Perhaps?`

5. A word containing a hyphen is split on each `-`. Each piece is title-cased on its own, so a small word inside the compound stays lowercase. A small word at the outer start or end of the whole line is still capitalized: `five-and` becomes `Five-And`.

   Input: `state-of-the-art design`

   Output: `State-of-the-Art Design`

6. A word containing `/`, but not `//`, is split on each slash. Each piece is title-cased on its own, so small words on either side of the slash stay lowercase.

   Input: `a title and/or string`

   Output: `A Title and/or String`

7. A word containing `//` is not split on the slash. Only its first letter is capitalized, so the text after `//` is not treated as a new word.

   Input: `visit http://foo today`

   Output: `Visit Http://foo Today`

8. A word that starts with `d`, `o`, or `l`, then `'` or `‘`, then letters, optionally ending in `'s`, is recased around the apostrophe. The first letter becomes lowercase for `d` and `l`, and uppercase for `o`. The letter immediately after the apostrophe becomes uppercase, and every later character keeps its original case. A word that does not start with one of those three letters, such as `it's fine`, is ordinary title case and becomes `It's Fine`.

   Input: `L'grange`

   Output: `l'Grange`

9. When a whole line has no lowercase letters, a token made of uppercase initials and periods, such as `D.C.`, is copied unchanged. The other words are still title-cased. On a line that is not entirely uppercase, the same dotted token is left as written because of its internal periods: `see d.c. now` becomes `See d.c. Now`.

   Input: `WASHINGTON, D.C. SHOULD BE FIXED BUT MIGHT BE A PROBLEM`

   Output: `Washington, D.C. Should Be Fixed but Might Be a Problem`

10. When a whole line has no lowercase letters, the remaining words are lowercased before the usual title-casing rules run. A small word such as `and` therefore ends up lowercase.

    Input: `THIS IS ALL CAPS AND SHOULD BE ADDRESSED`

    Output: `This Is All Caps and Should Be Addressed`

11. A word of more than two letters that contains only consonants is uppercased. For this test, `a`, `e`, `i`, `o`, `u`, and `y` are vowels. A two-letter consonant word stays ordinary title case, so `st` becomes `St`. A word that contains `y`, such as `rhythm`, becomes `Rhythm`.

    Input: `Words with all consonants like cnn are acronyms`

    Output: `Words With All Consonants Like CNN Are Acronyms`

12. When the line is not entirely uppercase, a word that already contains an uppercase letter after another letter is left unchanged. This keeps mixed-case names and short forms such as `AT&T`: `What is AT&T's problem?` becomes `What Is AT&T's Problem?`.

    Input: `iTunes should be unmolested`

    Output: `iTunes Should Be Unmolested`

13. A word containing a letter, a period, and another letter is left unchanged. That includes a host name. It also keeps a URL that contains both `//` and a dotted host intact: `this is http://foo.com` becomes `This Is http://foo.com`.

    Input: `this is just an example.com`

    Output: `This Is Just an example.com`

14. Space characters between words on the same line are preserved. A tab stays a tab rather than becoming a normal space.

    Input: `"text\twith\ttabs"`

    Output: `"Text\tWith\tTabs"`

15. Lines are separated with `\n`. A `\r\n` pair is also rejoined as a single `\n`, so `hello\r\nworld` becomes `Hello\nWorld`. By default, a run of line breaks is collapsed and blank lines are removed.

    Input: `"Line number one\n\nand Line three\n"`

    Output: `"Line Number One\nAnd Line Three\n"`

16. Passing `preserve_blank_lines=True` keeps empty lines between the title-cased lines.

    Input: `titlecase("Line number one\n\nand Line three\n", preserve_blank_lines=True)`

    Output: `"Line Number One\n\nAnd Line Three\n"`

17. Passing `normalise_space_characters=True` joins the words of each line with a single normal space, replacing tabs and other space characters.

    Input: `titlecase("text\twith\ttabs", normalise_space_characters=True)`

    Output: `"Text With Tabs"`

18. A word that starts with `Mc`, `mc`, or `MC`, followed by at least two more word characters, is given an `Mc` prefix. The remainder of the word is title-cased.

    Input: `oblon, spivak, mcclelland, maier & neustadt`

    Output: `Oblon, Spivak, McClelland, Maier & Neustadt`
