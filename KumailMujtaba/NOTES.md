# titlecase notes 

## Project Information
Project: python-titlecase
Repository: https://github.com/ppannuto/python-titlecase
Commit SHA: 42f43e2de55bf003b286c6f8e8d8b2d26676a167 2024-04-05T22:03:59-07:00

## Licence

The MIT License (MIT)

## Rules

`titlecase` handles the text line by line, then word by word. For each word it applies the first matching word rule and leaves that word alone afterwards. Line rules run after the words of that line are assembled.

1. Consecutive line breaks collapse into one break, so a blank line drops out. With `preserve_blank_lines=True`, every line break stays, including blank lines.
   - Input: `Line one\n\nLine three`
   - Output: `Line One\nLine Three`
   - Output with `preserve_blank_lines=True`: `Line One\n\nLine Three`

2. The original space characters between words stay in place, including tabs and other Unicode spaces. With `normalise_space_characters=True`, the words are rejoined with a single ordinary space.
   - Input: `text\twith\ttabs`
   - Output: `Text\tWith\tTabs`
   - Output with `normalise_space_characters=True`: `Text With Tabs`

3. A `callback(word, all_caps=...)` result is used as the word whenever the callback returns one. That result is kept through the first-and-last small-word step as well.
   - Input: `a simple udp wrapper`, callback returns `UDP` for `udp`
   - Output: `A Simple UDP Wrapper`

4. On a line written entirely in capitals, a run of initials stays in capitals. The surrounding words still go through the later rules.
   - Input: `WASHINGTON, D.C. SHOULD BE FIXED`
   - Output: `Washington, D.C. Should Be Fixed`

5. A word that starts with `o`, an apostrophe (`'` or `‘`), and more letters (optionally ending in `'s`) is capitalised on the `o` and on the letter after the apostrophe. Any letters after that stay as written.
   - Input: `my name is o'reilly`
   - Output: `My Name Is O'Reilly`

6. The same apostrophe shape starting with `d` or `l` keeps that first letter lowercase and capitalises the letter after the apostrophe.
   - Input: `l'grange`
   - Output: `l'Grange`

7. A word starting with `Mc`, `mc`, or `MC`, followed by at least two more letters, is written with `Mc` and the remainder is title-cased.
   - Input: `mcclelland`
   - Output: `McClelland`

8. `Mr`, `Mrs`, `Ms`, and `Dr`, in any case, are written with a capital first letter and the rest of the letters unchanged.
   - Input: `mr and mrs smith`
   - Output: `Mr and Mrs Smith`

9. A word that contains a letter, a period, and another letter stays as written. That covers hostnames and similar tokens.
   - Input: `this is just an example.com`
   - Output: `This Is Just an example.com`

10. When the line contains a lowercase letter, a word that already has a capital letter later in the word stays as written. This keeps mixed-case names and short forms such as `iTunes`, `AT&T`, and `Q&A`.
    - Input: `iTunes should be unmolested`
    - Output: `iTunes Should Be Unmolested`

11. These small words are lowercased: `a`, `an`, `and`, `as`, `at`, `but`, `by`, `en`, `for`, `if`, `in`, `of`, `on`, `or`, `the`, `to`, `v`, `v.`, `via`, `vs`, `vs.`. The list follows the New York Times Manual of Style, plus `v` and `vs`.
    - Input: `this vs. that`
    - Output: `This vs. That`

12. A word that contains `/` and does not contain `//` is split on each `/`. Each piece is title-cased on its own, then the pieces are joined with `/` again. A token that contains `//`, such as a URL, stays one word and is then subject to the other word rules (a URL with an internal period stays as written under rule 9).
    - Input: `word/word`
    - Output: `Word/Word`

13. A word that contains `-` is split on each `-`. Each piece is title-cased on its own, then the pieces are joined with `-` again. Small words in the middle of the compound stay lowercase.
    - Input: `end-to-end`
    - Output: `End-to-End`

14. On a line written entirely in capitals, a word that earlier rules did not already settle is lowercased before the remaining rules run, so the line comes back in title case.
    - Input: `THIS IS ALL CAPS`
    - Output: `This Is All Caps`

15. A word of only consonants, longer than two letters, is treated as an acronym and uppercased. `a`, `e`, `i`, `o`, `u`, and `y` count as vowels, so `cnn` qualifies and `st` (two letters) does not.
    - Input: `words like cnn`
    - Output: `Words Like CNN`

16. Any other word has its first letter capitalised. Punctuation before that letter stays put, and a word that starts with a digit keeps that digit, so `34th` stays `34th`.
    - Input: `hello world`
    - Output: `Hello World`

17. With `small_first_last` left at its default (`True`), a small word at the start of the line and a small word at the end of the line are capitalised. Leading punctuation stays in front of the first word (`'by` becomes `'By'`), and one trailing punctuation mark can follow the last small word (`of?` becomes `Of?`). Pieces inside a `/` or `-` split are title-cased with this step turned off, so only the ends of the whole line are affected.
    - Input: `a tale of`
    - Output: `A Tale Of`

18. After the line is joined, a small word that opens a sub-phrase is capitalised. A sub-phrase starts after `:`, `.`, `;`, `?`, `!`, or a dash (`-`, `–`, `‒`, `—`, `―`) followed by a space.
    - Input: `Starting Sub-Phrase With a Small Word: a Trick, Perhaps?`
    - Output: `Starting Sub-Phrase With a Small Word: A Trick, Perhaps?`

19. The finished lines are joined with a single `\n`.
    - Input: `this shouldn't\nget mangled`
    - Output: `This Shouldn't\nGet Mangled`
