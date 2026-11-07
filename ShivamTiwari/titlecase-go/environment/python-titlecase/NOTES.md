# Titlecase notes

## Source

- Repository: https://github.com/ppannuto/python-titlecase
- SHA: 42f43e2de55bf003b286c6f8e8d8b2d26676a167
- Date: 2024-04-05 22:03:59 -0700

## Licence

MIT (The MIT License (MIT))

Allowed: MIT, BSD, or Apache. This repository is MIT.

## Rules applied by `titlecase`

Each example below was run with `titlecase` at the SHA above. All 22 matched.

Small words, left lowercase except where a later rule capitalizes them, are: a, an, and, as, at, but, by, en, for, if, in, of, on, or, the, to, v, v., via, vs, vs. That list is the New York Times Manual of Style list, plus `vs` and `v`.

1. Each line is title-cased on its own, and lines are joined back with `\n`.
   - Input: `this shouldn't\nget mangled`
   - Output: `This Shouldn't\nGet Mangled`

2. By default, consecutive line breaks collapse, so blank lines are dropped.
   - Input: `Line number one\n\nand Line three\n`
   - Output: `Line Number One\nAnd Line Three\n`

3. With `preserve_blank_lines=True`, every line break is kept, including blank lines.
   - Input: `Line number one\n\nand Line three\n`
   - Output: `Line Number One\n\nAnd Line Three\n`

4. By default, the original space characters between words are kept (spaces, tabs, and other separators).
   - Input: `text\twith\ttabs`
   - Output: `Text\tWith\tTabs`

5. With `normalise_space_characters=True`, words are rejoined with a single ordinary space.
   - Input: `text\twith\ttabs`
   - Output: `Text With Tabs`

6. If `callback` returns a string for a word, that string is used as-is. It is not changed by the first-word or last-word rules. Returning no value leaves the word to the rules below.
   - Input: `a simple tcp and udp wrapper` with a callback that returns `TCP` and `UDP`
   - Output: `A Simple TCP and UDP Wrapper`

7. On a line that is entirely uppercase, tokens of initials such as `A.B` or `D.C.` are left unchanged.
   - Input: `WASHINGTON, D.C. SHOULD BE FIXED BUT MIGHT BE A PROBLEM`
   - Output: `Washington, D.C. Should Be Fixed but Might Be a Problem`

8. A word that starts with `o`, `d`, or `l` plus an apostrophe is recapitalized around that apostrophe. If the first letter is a vowel (`o`), both that letter and the letter after the apostrophe are capitalized. A trailing `'s` is kept.
   - Input: `my name is o'reilly`
   - Output: `My Name Is O'Reilly`

9. If that first letter is a consonant (`d` or `l`), it is lowercased and the letter after the apostrophe is capitalized.
   - Input: `l'grange l'grange l'Grange l'Grange`
   - Output: `l'Grange l'Grange l'Grange l'Grange`

10. A word that starts with `Mc`, `mc`, or `MC` keeps that prefix as `Mc`, and the remainder is title-cased.
    - Input: `oblon, spivak, mcclelland, maier & neustadt`
    - Output: `Oblon, Spivak, McClelland, Maier & Neustadt`

11. `Mr`, `Mrs`, `Ms`, `M`, and `Dr` (any capitalization) keep the rest of the token as written and only force the first letter to uppercase.
    - Input: `Mr mr Mrs Ms Dr dr`
    - Output: `Mr Mr Mrs Ms Dr Dr`

12. A word that contains an inline period between letters, such as a hostname, is left unchanged.
    - Input: `this is just an example.com`
    - Output: `This Is Just an example.com`

13. On a line that is not entirely uppercase, a word that already contains an uppercase letter after other letters is left unchanged.
    - Input: `iTunes should be unmolested`
    - Output: `iTunes Should Be Unmolested`

14. A small word is written in lowercase.
    - Input: `this v that`
    - Output: `This v That`

15. A single slash splits a word into parts, and each part is title-cased without forcing a small word at either end of that part. A double slash is not split.
    - Input: `a title and/or string`
    - Output: `A Title and/or String`

16. A hyphen splits a word the same way: each part is title-cased, and a small word in the middle stays lowercase.
    - Input: `end-to-end`
    - Output: `End-to-End`

17. On a line that is entirely uppercase, a word that was not already preserved is lowercased before the remaining capitalization rules run.
    - Input: `THIS IS ALL CAPS AND SHOULD BE ADDRESSED`
    - Output: `This Is All Caps and Should Be Addressed`

18. A word made only of consonants, longer than two letters, is uppercased as an acronym. `y` counts as a vowel, so a short word such as `St` is not treated as an acronym.
    - Input: `Words with all consonants like cnn are acronyms`
    - Output: `Words With All Consonants Like CNN Are Acronyms`

19. Any other word has its first letter capitalized. Leading punctuation stays in front of that letter, and the rest of the word is left as it is.
    - Input: `Q&A with steve jobs: 'that's what happens in technology'`
    - Output: `Q&A With Steve Jobs: 'That's What Happens in Technology'`

20. A small word that is the first word of a line is capitalized, including when punctuation precedes it. This is skipped for a word the callback already fixed, and for the parts of a slash or hyphen split.
    - Input: `a thing`
    - Output: `A Thing`

21. A small word that is the last word of a line is capitalized, including when punctuation follows it.
    - Input: `Small word at end is nothing to be afraid of`
    - Output: `Small Word at End Is Nothing to Be Afraid Of`

22. A small word that starts a sub-phrase is capitalized. A sub-phrase starts after `:`, `.`, `;`, `?`, `!`, or a dash (`-`, `–`, `‒`, `—`, `―`) followed by a space.
    - Input: `Starting Sub-Phrase With a Small Word: a Trick, Perhaps?`
    - Output: `Starting Sub-Phrase With a Small Word: A Trick, Perhaps?`

## Examples the notes got wrong

None. Every listed input and output was checked against this commit and matched.
