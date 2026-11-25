# Titlecase notes

## Licence

The MIT License (MIT)

## Rules applied by `titlecase`

The function title-cases text. Small words are left lowercase in the middle of a phrase. That list comes from the New York Times Manual of Style, plus `v`, `v.`, `vs`, `vs.`, and `via`: `a`, `an`, `and`, `as`, `at`, `but`, `by`, `en`, `for`, `if`, `in`, `of`, `on`, `or`, `the`, `to`, `v`, `v.`, `via`, `vs`, `vs.`.

1. **Lines.** The text is split on newlines. Consecutive newlines are collapsed, so a blank line is dropped. The processed lines are joined with a single newline. Pass `preserve_blank_lines=True` to keep each blank line.
   - Input: `Line number one\n\nand Line three`
   - Output: `Line Number One\nAnd Line Three`

2. **Whitespace between words.** Each line is split on whitespace, and the original space characters are put back between words. Pass `normalise_space_characters=True` to replace them with ordinary spaces.
   - Input: `text\twith\ttabs`
   - Output: `Text\tWith\tTabs`

3. **Callback.** If `callback(word, all_caps=...)` returns a non-empty string, that string is used for the word. It is then left alone by the small-word fixes at the start and end of the line.
   - Input: `a simple tcp and udp wrapper`, with a callback that returns `UDP` for that word
   - Output: `A Simple TCP and UDP Wrapper`

4. **All-caps lines.** A line that is already entirely uppercase is treated as all caps. Words that are not kept by an earlier rule are lowercased before they are capitalized, so a shouted line becomes title case.
   - Input: `THIS IS ALL CAPS AND SHOULD BE ADDRESSED`
   - Output: `This Is All Caps and Should Be Addressed`

5. **Initials on an all-caps line.** On an all-caps line, a word that is a run of uppercase initials with periods (for example `D.C.`) is left unchanged.
   - Input: `WASHINGTON, D.C. SHOULD BE FIXED BUT MIGHT BE A PROBLEM`
   - Output: `Washington, D.C. Should Be Fixed but Might Be a Problem`

6. **Apostrophes in `d'`, `l'`, and `o'` words.** A word that starts with `d`, `l`, or `o`, then `'` or `‘`, then letters (optionally ending in `'s`) is rewritten so the letter after the apostrophe is capitalized. `d` and `l` stay lowercase. `o` is capitalized. Any characters after that letter are left as they are.
   - Input: `l'grange`
   - Output: `l'Grange`

7. **`Mc` prefix.** A word that starts with `Mc`, `mc`, or `MC` and then at least two more word characters becomes `Mc` plus the title case of the rest.
   - Input: `mcclelland`
   - Output: `McClelland`

8. **Honorifics.** `Mr`, `Mrs`, `Ms`, and `Dr`, in any capitalization and without a trailing period, keep the rest of their letters and only have the first letter capitalized.
   - Input: `dr`
   - Output: `Dr`

9. **Words left as written.** A word that contains a period between two letters (a domain name, for example) is left unchanged. A word that already has a capital letter after its first letter is also left unchanged, unless the whole line is all caps.
   - Input: `iTunes should be unmolested`
   - Output: `iTunes Should Be Unmolested`

10. **Small words.** A word on the small-word list is lowercased. Later rules capitalize it again when it is the first or last word of the line, or the first word of a sub-phrase.
    - Input: `this is a test`
    - Output: `This Is a Test`

11. **Slashes.** A word that contains `/` and does not contain `//` is split on each slash. Each part is title-cased on its own and the parts are joined again with `/`. A word that contains `//` is not split this way.
    - Input: `word/word`
    - Output: `Word/Word`

12. **Hyphens.** A word that contains `-` is split on each hyphen. Each part is title-cased on its own and the parts are joined again with `-`. Inside that recursion, a small word is not forced to a capital just because it is first or last in its part, so a small word in the middle stays lowercase.
    - Input: `end-to-end`
    - Output: `End-to-End`

13. **All-consonant acronyms.** A word longer than two letters whose letters are all consonants (`a`, `e`, `i`, `o`, `u`, and `y` count as vowels) is uppercased. A shorter consonant word, such as `St`, is capitalized like an ordinary word.
    - Input: `Words with all consonants like cnn are acronyms`
    - Output: `Words With All Consonants Like CNN Are Acronyms`

14. **Ordinary words.** Any remaining word has its first letter capitalized. Leading punctuation is skipped, so a quote or similar mark does not block that capital. The rest of the word is left as it is. A word that starts with a digit, such as `34th`, has no letter to capitalize and stays as it is.
    - Input: `hello world`
    - Output: `Hello World`

15. **Small word at the start.** After the words are processed, a small word at the start of the line is capitalized. Leading punctuation, including an opening quote, stays in front of that capital. A word supplied by the callback is skipped.
    - Input: `'by the Way, small word at the start but within quotes.'`
    - Output: `'By the Way, Small Word at the Start but Within Quotes.'`

16. **Small word at the end.** A small word at the end of the line is capitalized, including when punctuation follows it. A word supplied by the callback is skipped.
    - Input: `Small word at end is nothing to be afraid of`
    - Output: `Small Word at End Is Nothing to Be Afraid Of`

17. **Small word after a sub-phrase break.** A small word that comes right after a colon, period, semicolon, question mark, exclamation mark, or dash (`-`, `–`, `‒`, `—`, `―`) and a space is capitalized.
    - Input: `Starting Sub-Phrase With a Small Word: a Trick, Perhaps?`
    - Output: `Starting Sub-Phrase With a Small Word: A Trick, Perhaps?`

18. **URLs.** The code does not look for a scheme or host prefix such as `http`, `https`, or `www`. A whitespace-delimited word is left unchanged when `INLINE_PERIOD` matches anywhere in it: a letter, a period, and another letter. With the third-party `regex` module that pattern is `[\p{Letter}][.][\p{Letter}]`. When `titlecase` falls back to the standard-library `re` module, the pattern is `[\w][.][\w]`. The whole word is kept, so a dotted URL keeps its scheme, `www`, slashes, and host together. `http://example.com`, `https://example.com`, and `www.example.com` all match. A URL with no letter-period-letter sequence, such as `http://example`, does not match and is not kept as written.
    - Input: `visit http://example.com for the details`
    - Output: `Visit http://example.com for the Details`
