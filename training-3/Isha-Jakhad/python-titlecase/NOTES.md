# Notes

## Repository

URL: https://github.com/ppannuto/python-titlecase

Commit SHA: 42f43e2de55bf003b286c6f8e8d8b2d26676a167

Commit Date: 2024-04-05T22:03:59-07:00


## Licence

The MIT License (MIT)

## Rules `titlecase()` applies

Rules run in this order. Each example was produced by calling `titlecase()` from this package.

1. By default, a run of carriage returns and line feeds is one line break, so a blank line is removed. `\r\n` is one break. Title-cased lines are joined with `\n`.

   Input: `"Line number one\n\nand Line three\n"`

   Output: `"Line Number One\nAnd Line Three\n"`

2. With `preserve_blank_lines=True`, every `\r` or `\n` is its own break, so a blank line stays. A `\r\n` pair is two breaks.

   Input: `titlecase("Line number one\n\nand Line three\n", preserve_blank_lines=True)`

   Output: `"Line Number One\n\nAnd Line Three\n"`

3. Whitespace between words on a line is kept character for character.

   Input: `"text\twith\ttabs"`

   Output: `"Text\tWith\tTabs"`

4. With `normalise_space_characters=True`, the words of a line are joined with a single ordinary space.

   Input: `titlecase("text\twith\ttabs", normalise_space_characters=True)`

   Output: `"Text With Tabs"`

5. When `callback(word, all_caps=...)` returns a truthy value, that value is the word's result. A falsy return leaves the word to the later rules. A truthy result is immutable: the first-word and last-word small-word capitalization below does not change it.

   Input: `titlecase("a simple tcp and udp wrapper", callback=callback)` with

   ```python
   def callback(word, **kwargs):
    if word.upper() in ("TCP", "UDP"):
        return word.upper()
   ```

   Output: `"A Simple TCP and UDP Wrapper"`

6. When the whole line is uppercase (`line.upper() == line`), a word that is entirely one or more initialisms of the form `A.` or `A.B` is left unchanged. The implementation uses Unicode uppercase-letter matching when the optional `regex` package is available, and the ASCII pattern `^(?:[A-Z]\.|[A-Z]\.[A-Z])+$` as a fallback when using Python's built-in `re` module.

    Input: `"WASHINGTON, D.C. SHOULD BE FIXED BUT MIGHT BE A PROBLEM"`

    Output: `"Washington, D.C. Should Be Fixed but Might Be a Problem"`

7. A word that is `d`, `o`, or `l`, then `'` or `‘`, then letters, with an optional suffix matching `['s]{2}` at the end, is rewritten in place. The letter after the apostrophe is uppercased. A leading `o` is uppercased. A leading `d` or `l` is lowercased. Characters after that letter stay as they were.

    Input: `"my name is o'reilly"`

    Output: `"My Name Is O'Reilly"`

8. A word that starts with `Mc`, `mc`, or `MC`, followed by at least two more characters, becomes that prefix capitalized as `Mc` plus `titlecase()` of the remainder.

   Input: `"oblon, spivak, mcclelland, maier & neustadt"`

   Output: `"Oblon, Spivak, McClelland, Maier & Neustadt"`

9. A word that is entirely `m`, `mr`, `mrs`, `ms`, or `dr`, in any case, keeps every character after the first and has its first character uppercased.

   Input: `"MRS JONES"`

   Output: `"MRS Jones"`

10. A word that contains a letter, a period, and a letter (`[\w][.][\w]`) is left unchanged, including on an all-uppercase line.

    Input: `"this is just an example.com"`

    Output: `"This Is Just an example.com"`

11. When the line is not all uppercase, a word that starts with optional punctuation from the function's punctuation set and then has an uppercase ASCII letter after another ASCII letter is left unchanged. The implementation uses Unicode letter categories when the optional `regex` package is available, and the ASCII pattern `[%s]*?[a-zA-Z]+[A-Z]+?` with the punctuation set filled in as a fallback when using Python's built-in `re` module.

    Input: `"iTunes should be unmolested"`

    Output: `"iTunes Should Be Unmolested"`

12. A word in the small-word list is lowercased. The list is `a`, `an`, `and`, `as`, `at`, `but`, `by`, `en`, `for`, `if`, `in`, `of`, `on`, `or`, `the`, `to`, `v`, `v.`, `via`, `vs`, and `vs.`. The function docstring attributes that list to the New York Times Manual of Style, plus `vs` and `v`.

    Input: `"this vs. that"`

    Output: `"This vs. That"`

13. A word that contains `/` and does not contain `//` is split on `/`. Each part is passed through `titlecase()` with `small_first_last=False`, and the parts are joined with `/`.

    Input: `"word/word"`

    Output: `"Word/Word"`

14. A word that contains `-` is split on `-`. Each part is passed through `titlecase()` with `small_first_last=False`, and the parts are joined with `-`.

    Input: `"end-to-end"`

    Output: `"End-to-End"`

15. When the original line is all uppercase, a word that is still being processed is lowercased before the acronym test and the ordinary capitalization. Words already returned by an earlier rule keep the case that rule gave them.

    Input: `"THIS IS ALL CAPS AND SHOULD BE ADDRESSED"`

    Output: `"This Is All Caps and Should Be Addressed"`

16. A word of only consonants, longer than two characters, is uppercased. Consonants are the ASCII letters except `a`, `e`, `i`, `o`, `u`, and `y`. A shorter word such as `St` stays on the ordinary capitalization path.

    Input: `"words with all consonants like cnn are acronyms"`

    Output: `"Words With All Consonants Like CNN Are Acronyms"`

17. Any word still left has its first letter uppercased. Leading punctuation from the function's punctuation set stays in front of that letter. The pattern is `^[%s]*?([\w])` with that set filled in, and the whole match is uppercased.

    Input: `"hello world"`

    Output: `"Hello World"`

18. When `small_first_last` is true (the default), a small word at the start of the line is capitalized. Leading punctuation may sit in front of it. This step is skipped when a callback made that word immutable.

    Input: `"'by the Way, small word at the start but within quotes.'"`

    Output: `"'By the Way, Small Word at the Start but Within Quotes.'"`

19. When `small_first_last` is true, a small word at the end of the line is capitalized. One trailing punctuation character may follow it and stays in the word. This step is skipped when a callback made that word immutable.

    Input: `"Small word at end is nothing to be afraid of"`

    Output: `"Small Word at End Is Nothing to Be Afraid Of"`

20. A small word that follows a subphrase mark and a space is capitalized. The mark is one of `:`, `.`, `;`, `?`, `!`, `-`, `–`, `‒`, `—`, or `―`.

    Input: `"Starting Sub-Phrase With a Small Word: a Trick, Perhaps?"`

    Output: `"Starting Sub-Phrase With a Small Word: A Trick, Perhaps?"`
