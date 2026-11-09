# cdRepository Information

Repository URL: https://github.com/ppannuto/python-titlecase
Commit SHA: 42f43e2de55bf003b286c6f8e8d8b2d26676a167
Commit Date: 2024-04-05T22:03:59-07:00

# titlecase notes

## Licence

The MIT License (MIT)

## Rules applied by `titlecase`

1. Each line is title-cased on its own, then the lines are joined with `\n`.
   - Input: `this shouldn't\nget mangled`
   - Output: `This Shouldn't\nGet Mangled`

2. Consecutive line breaks are collapsed, so blank lines are dropped. Pass `preserve_blank_lines=True` to keep them.
   - Input: `Line number one\n\nand Line three\n`
   - Output: `Line Number One\nAnd Line Three\n`
   - Output with `preserve_blank_lines=True`: `Line Number One\n\nAnd Line Three\n`

3. Words are split on whitespace. That whitespace is kept, including tabs and other space characters. Pass `normalise_space_characters=True` to join the words with ordinary spaces instead.
   - Input: `text\twith\ttabs`
   - Output: `Text\tWith\tTabs`
   - Output with `normalise_space_characters=True`: `Text With Tabs`

4. If `callback(word, all_caps=...)` returns a non-empty string, that string is used for the word. It is then left unchanged, including by the first-word and last-word capitalization in rule 16.
   - Input: `a simple tcp and udp wrapper`, with a callback that returns `TCP` for `tcp` and `UDP` for `udp`
   - Output: `A Simple TCP and UDP Wrapper`

5. When the whole line is uppercase, a word that is a run of initials is kept. An initial is one capital letter and a period (`A.`), or one capital, a period, and another capital (`A.B`), repeated.
   - Input: `SEE A.B. TODAY`
   - Output: `See A.B. Today`

6. A word that starts with `d`, `o`, or `l` and an apostrophe (`'` or `‘`), optionally ending in `'s`, is recased around the apostrophe. If the first letter is a consonant (`d` or `l`), it stays lowercase and the letter after the apostrophe is capitalized. If the first letter is a vowel (`o`), both that letter and the letter after the apostrophe are capitalized. Any characters after the third are left as they are.
   - Input: `d'artagnan`
   - Output: `d'Artagnan`

7. A word that starts with `Mc` or `MC`, followed by at least two more characters, is written as `Mc` plus the title-cased remainder.
   - Input: `mcdonald`
   - Output: `McDonald`

8. `Mr`, `Mrs`, `Ms`, and `Dr` (any capitalization that matches those forms) keep every character after the first, and the first character is capitalized.
   - Input: `mrs smith`
   - Output: `Mrs Smith`

9. A word that contains an internal period between two letters (for example a hostname or `D.C.`) is left unchanged.
   - Input: `D.C. weather`
   - Output: `D.C. Weather`

10. When the line is not entirely uppercase, a word that already contains a capital letter after its first letters is left unchanged.
    - Input: `iPhone release`
    - Output: `iPhone Release`

11. These small words are lowercased: `a`, `an`, `and`, `as`, `at`, `but`, `by`, `en`, `for`, `if`, `in`, `of`, `on`, `or`, `the`, `to`, `v`, `v.`, `via`, `vs`, `vs.`. The list is the New York Times Manual of Style list, plus `v` and `vs`.
    - Input: `this via that`
    - Output: `This via That`

12. A word that contains `/` but not `//` is split on each slash, and each piece is title-cased on its own. A `//` is not split.
    - Input: `word/word`
    - Output: `Word/Word`

13. A hyphenated word is split on `-`, and each piece is title-cased on its own. Small words inside the compound stay lowercase, because that recursive call does not capitalize the first and last piece.
    - Input: `end-to-end`
    - Output: `End-to-End`

14. When the whole line is uppercase, a word that was not already handled above is lowercased before the acronym and ordinary-word rules run.
    - Input: `THIS IS ALL CAPS AND SHOULD BE ADDRESSED`
    - Output: `This Is All Caps and Should Be Addressed`

15. A word made only of consonants and longer than two letters is treated as an acronym and fully uppercased. `a`, `e`, `i`, `o`, `u`, and `y` count as vowels, so a two-letter word such as `st` is not treated as an acronym.
    - Input: `html and css`
    - Output: `HTML and CSS`

16. Any remaining word is capitalized on its first letter. Punctuation before that letter is left in place, and a word with no letter (such as `34th`) is unchanged.
    - Input: `hello world`
    - Output: `Hello World`

17. After the words are processed, a small word in the first position or the last position of the line is capitalized, unless a callback marked that word as immutable (rule 4). Leading punctuation before a first small word is kept.
    - Input: `the end of the`
    - Output: `The End of The`

18. A small word that follows a subphrase break and a space is capitalized. The break characters are `:`, `;`, `.`, `?`, `!`, and the dashes `-`, `–`, `‒`, `—`, and `―`.
    - Input: `hello: the world`
    - Output: `Hello: The World`
