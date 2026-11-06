# Titlecase notes

## Licence

The MIT License (MIT)

## Rules

Small words are `a`, `an`, `and`, `as`, `at`, `but`, `by`, `en`, `for`, `if`, `in`, `of`, `on`, `or`, `the`, `to`, `v`, `v.`, `via`, `vs`, and `vs.` (the New York Times list, plus `v` and `vs`). The function applies these rules to each word:

1. A callback that returns a new word replaces that word, and later first-word and last-word fixes leave that result alone.
   - Input: `at&t`, with a callback that returns `AT&T`
   - Output: `AT&T`

2. On a fully uppercase line, an initialism of capital letters and periods (such as `A.B` or `D.C.`) is kept as written.
   - Input: `WASHINGTON, D.C. SHOULD BE FIXED BUT MIGHT BE A PROBLEM`
   - Output: `Washington, D.C. Should Be Fixed but Might Be a Problem`

3. A word matching `d'…` or `l'…` (straight or curly apostrophe, optional `'s`) keeps the first letter lowercase and capitalizes the letter after the apostrophe.
   - Input: `l'grange`
   - Output: `l'Grange`

4. A word matching `o'…` capitalizes both the `o` and the letter after the apostrophe.
   - Input: `o'grange`
   - Output: `O'Grange`

5. A word that starts with `Mc` or `MC`, followed by at least two more characters, is written as `Mc` plus the title-cased remainder.
   - Input: `mcclelland`
   - Output: `McClelland`

6. `Mr`, `Mrs`, `Ms`, and `Dr` keep the rest of their spelling and force only the first letter to uppercase.
   - Input: `dr`
   - Output: `Dr`

7. A word that contains a letter, a period, and another letter is left unchanged.
   - Input: `this is just an example.com`
   - Output: `This Is Just an example.com`

8. On a line that is not fully uppercase, a mixed-case word that already has a capital later in the word is left unchanged.
   - Input: `iTunes should be unmolested`
   - Output: `iTunes Should Be Unmolested`

9. A small word is written in lowercase.
   - Input: `this vs that`
   - Output: `This vs That`

10. A word that contains `/` but not `//` is split on `/`, and each part is title-cased on its own.
    - Input: `word/word`
    - Output: `Word/Word`

11. A word that contains `//` is not split on `/`, so a URL stays intact.
    - Input: `this is http://foo.com`
    - Output: `This Is http://foo.com`

12. A hyphenated word is split on `-`, and each part is title-cased on its own. Small words inside the compound stay lowercase.
    - Input: `end-to-end`
    - Output: `End-to-End`

13. On a fully uppercase line, a remaining word is lowercased before the later capitalization rules run.
    - Input: `THIS IS ALL CAPS AND SHOULD BE ADDRESSED`
    - Output: `This Is All Caps and Should Be Addressed`

14. A word longer than two letters that is made only of consonants (`y` counts as a vowel) is uppercased as an acronym.
    - Input: `words like cnn`
    - Output: `Words Like CNN`

15. A consonant-only word of two letters or fewer, such as `st`, is capitalized as a normal word.
    - Input: `foo bar 5th st`
    - Output: `Foo Bar 5th St`

16. Any other word is capitalized: the first letter is uppercased, including when punctuation comes before it, and the rest of the word is left as given.
    - Input: `'by the way'`
    - Output: `'By the Way'`

17. When `small_first_last` is on (the default), a small word that is the first or last word of the line is capitalized. Slash and hyphen parts are title-cased with this turned off.
    - Input: `Small word at end is nothing to be afraid of`
    - Output: `Small Word at End Is Nothing to Be Afraid Of`

18. A small word that starts a sub-phrase is capitalized. A sub-phrase begins after `:`, `.`, `;`, `?`, `!`, or a dash (`-`, `–`, `‒`, `—`, `―`) followed by a space.
    - Input: `Starting Sub-Phrase With a Small Word: a Trick, Perhaps?`
    - Output: `Starting Sub-Phrase With a Small Word: A Trick, Perhaps?`

19. Each line is title-cased on its own, and the lines are joined back with newlines.
    - Input: `this shouldn't\nget mangled`
    - Output: `This Shouldn't\nGet Mangled`

20. Blank lines are collapsed by default.
    - Input: `Line number one\n\nand Line three\n`
    - Output: `Line Number One\nAnd Line Three\n`

21. `preserve_blank_lines=True` keeps blank lines.
    - Input: `Line number one\n\nand Line three\n`
    - Output: `Line Number One\n\nAnd Line Three\n`

22. The original space characters between words are kept.
    - Input: `text\twith\ttabs`
    - Output: `Text\tWith\tTabs`

23. `normalise_space_characters=True` rejoins the words with a single ordinary space.
    - Input: `text\twith\ttabs`
    - Output: `Text With Tabs`
