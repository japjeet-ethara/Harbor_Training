# `titlecase()` notes

## Licence

**The MIT License (MIT)**

`LICENSE.txt` names the licence "The MIT License (MIT)" and copyrights the work as Copyright (c) 2021 Patrick William Pannuto. The module docstring points at the same licence.

## Rules `titlecase()` applies

`titlecase(text, callback=None, small_first_last=True, preserve_blank_lines=False, normalise_space_characters=False)` title-cases text one line at a time. Each line is split into words on whitespace. **For each word, the first matching rule wins** and the later word rules are skipped. After every word has been handled, the line-level small-word fixes run.

A line counts as all-caps when `line.upper() == line`. That flag is decided per line.

The small words, from the New York Times Manual of Style plus `v` and `vs`, are:

`a`, `an`, `and`, `as`, `at`, `but`, `by`, `en`, `for`, `if`, `in`, `of`, `on`, `or`, `the`, `to`, `v`, `v.`, `via`, `vs`, `vs.`

### 1. Line breaks are split, then joined with `\n`

A run of one or more `\r` or `\n` characters is one line break, so a blank line is dropped. With `preserve_blank_lines=True`, every single `\r` or `\n` is its own break, so blank lines stay. Because `\r` and `\n` are separate breaks in that mode, a Windows `\r\n` pair becomes two breaks. The processed lines are always joined with `\n`.

- Input: `Line number one\n\nand Line three\n`
- Output: `Line Number One\nAnd Line Three\n`
- Same input with `preserve_blank_lines=True`: `Line Number One\n\nAnd Line Three\n`

### 2. The original space between words is kept

Words are separated on whitespace, and those exact separator characters are put back. Tabs, non-breaking spaces, and repeated spaces stay as they were. With `normalise_space_characters=True`, the words are joined with one ordinary space.

- Input: `text\twith\ttabs`
- Output: `Text\tWith\tTabs`
- Same input with `normalise_space_characters=True`: `Text With Tabs`

### 3. A truthy callback result replaces the word

If `callback` is set, it is called as `callback(word, all_caps=all_caps)`. A truthy return value is used as the word and the remaining word rules are skipped. That word is also skipped by the first-word and last-word fixes in rules 16 and 17. `None` and `""` mean the callback has no opinion, and the normal rules run.

The sub-phrase fix in rule 18 runs on the finished line, so it can still capitalize a small word that the callback returned.

- Input: `a simple tcp and udp wrapper`, with a callback that returns `TCP` and `UDP` for those words
- Output: `A Simple TCP and UDP Wrapper`

### 4. Initials on an all-caps line stay as written

On an all-caps line, a word that is entirely initials is kept unchanged. The whole word must be a sequence of `X.` or `X.Y` groups, such as `A.`, `A.B`, `A.B.`, or `D.C.`.

- Input: `WASHINGTON, D.C. SHOULD BE FIXED BUT MIGHT BE A PROBLEM`
- Output: `Washington, D.C. Should Be Fixed but Might Be a Problem`

`D.C.` is kept by this rule. On a line that is not all-caps, a token such as `D.C.` is kept later by the inline-period rule instead.

### 5. `d'`, `o'`, and `l'` words get a fixed apostrophe shape

A whole word matching `d`, `o`, or `l`, then `'` or `‘`, then letters, with an optional `'s` at the end, is rebuilt:

- `d` and `l` are written in lowercase. `o` is a vowel, so it is written in uppercase.
- The first letter after the apostrophe is capitalized.
- Every character after that is copied unchanged, including a possessive `'s` and any later capitals.

- Input: `l'grange`
- Output: `l'Grange`
- Input: `my name is o'reilly`
- Output: `My Name Is O'Reilly`

`l'GranGe` stays `l'GranGe` because only the first letter of each piece is forced; the tail is copied.

### 6. An `Mc` prefix is normalized, and the rest is title-cased

A word that starts with `Mc`, `mc`, or `MC` and then has at least two more characters uses this rule. The prefix is passed through `str.capitalize`, so all three spellings become `Mc`. The remainder is passed back through `titlecase()` with first/last small-word capitalization enabled, including when the outer call turned that off.

`mc` and `mca` are too short for this rule and fall through to ordinary capitalization (`Mc`, `Mca`).

- Input: `mcclelland`
- Output: `McClelland`

`mcby` becomes `McBy` because the remainder `by` is a small word and the recursive call capitalizes a small word in first position.

### 7. `Mr`, `Mrs`, `Ms`, and `Dr` keep the rest of their spelling

Those four words match in any case, with nothing else in the word. The first character is uppercased and the remaining characters are copied unchanged, so `dr` becomes `Dr` and `DR` stays `DR`. A period is outside the match, so `Mr.` is handled by the ordinary first-letter rule.

- Input: `dr`
- Output: `Dr`

In the test string `Mr mr Mrs Ms Mss Dr dr , Mr. and Mrs. Person` → `Mr Mr Mrs Ms MSS Dr Dr , Mr. And Mrs. Person`, this rule produces the `Mr`, `Mrs`, `Ms`, and `Dr` forms. `Mss` is three consonants, so rule 14 produces `MSS`.

### 8. A word with a letter, a period, and another letter is left unchanged

If `letter.letter` occurs anywhere in the word, the word is copied through. Domains and URL tokens are kept, including their existing capitals.

- Input: `this is just an example.com`
- Output: `This Is Just an example.com`

The same rule keeps `this is http://foo.com` as `This Is http://foo.com`.

### 9. Internal capitals are kept when the line is not all-caps

If the line is not all-caps, a word that contains an uppercase letter after another letter is copied unchanged. This keeps camel case and names such as `iTunes`, `AT&T`, `AT&T's`, `OmniFocus`, and `MacDonalds`. There is no separate `Mac` prefix rule. `macdonalds` becomes `Macdonalds` by ordinary capitalization, while `MacDonalds` is kept by this rule.

On an all-caps line this rule is skipped, so the later lowercase-then-capitalize path runs: `ITUNES` becomes `Itunes`, and `KEEP AT&T PLEASE` becomes `Keep At&t Please`.

- Input: `iTunes should be unmolested`
- Output: `iTunes Should Be Unmolested`

### 10. Small words are lowercased

If the whole word is one of the small words listed above, it is written in lowercase. `v.` and `vs.` include the period. A small word with any other attached character, such as `of?`, is not a whole-word match.

- Input: `this v that`
- Output: `This v That`

The same list covers `this vs that` → `This vs That` and `this vs. that` → `This vs. That`.

### 11. `/` splits a word into parts, and `//` stays together

If the word contains `/` and does not contain `//`, it is split on `/`. Each part is title-cased with `small_first_last=False`, then the parts are joined with `/`. Small words inside the compound stay lowercase. A later first-word or last-word fix can still capitalize a small word at the very start or end of the line, so the whole string `and/or` becomes `And/Or`, while the same compound in the middle of a line stays `and/or`.

A word that contains `//` skips this split. `foo//bar` becomes `Foo//bar`.

- Input: `a title and/or string`
- Output: `A Title and/or String`

### 12. A hyphen splits a word into parts

If the word contains an ASCII hyphen `-`, it is split on `-`. Each part is title-cased with `small_first_last=False`, then joined with `-`. En dashes and em dashes are not split here. With spaces around them, they are separate tokens and rule 18 can capitalize a following small word.

- Input: `end-to-end`
- Output: `End-to-End`

`to` stays lowercase. In `word-of-mouth` the result is `Word-of-Mouth`.

### 13. Leftover words on an all-caps line are lowercased

If the line is all-caps and no earlier rule took the word, the word is lowercased before the acronym check and ordinary capitalization. That is what turns shouty text into title case. Words already returned by rules 4 through 12 keep the form those rules produced.

- Input: `THIS IS ALL CAPS AND SHOULD BE ADDRESSED`
- Output: `This Is All Caps and Should Be Addressed`

`AND` is lowercase because it is a small word (rule 10). `THIS` reaches this rule, becomes `this`, and is then capitalized.

### 14. A long all-consonant word is an acronym

After the all-caps lowercase step, a word longer than two characters whose every character is an ASCII consonant is uppercased. The letters `a`, `e`, `i`, `o`, `u`, and `y` are excluded from the consonant set, so `y` does not make an acronym. A digit or any other character anywhere in the word blocks the match. Two-letter consonant words stay on the ordinary path, which is why `St` is not forced to `ST`.

- Input: `Words with all consonants like cnn are acronyms`
- Output: `Words With All Consonants Like CNN Are Acronyms`

`FOO BAR 5TH ST` becomes `Foo Bar 5th St`. `html is tv` becomes `HTML Is Tv`. `NYC` becomes `Nyc`.

### 15. Otherwise the first letter is capitalized

The first letter is uppercased. Leading punctuation is left in front of that letter and is allowed before it. The rest of the word is copied unchanged, so digits, existing lowercase, and characters after the first letter stay put.

- Input: `2lmc Spool: 'gruber on OmniFocus and vapo(u)rware'`
- Output: `2lmc Spool: 'Gruber on OmniFocus and Vapo(u)rware'`

`gruber` becomes `Gruber` and `vapo(u)rware` becomes `Vapo(u)rware`. `2lmc` starts with a digit, so it stays `2lmc`. `OmniFocus` was already kept by rule 9. The same first-letter rule leaves `34th 3rd 2nd` as `34th 3rd 2nd`.

### 16. A small word at the start of the line is capitalized

When `small_first_last` is true (the default) and the line has at least one word, a small word at the start of the first word is capitalized. Leading punctuation stays in place. A word fixed by the callback is left as the callback wrote it.

With `small_first_last=False`, this fix is skipped: `a cat` stays `a Cat`. Slash and hyphen recursion pass `False` for this flag. The `Mc` recursion passes `True`.

- Input: `'by the Way, small word at the start but within quotes.'`
- Output: `'By the Way, Small Word at the Start but Within Quotes.'`

The leading `'` stays, and the small word `by` becomes `By`. A one-word line such as `a` becomes `A`.

### 17. A small word at the end of the line is capitalized

Under the same `small_first_last` flag, a small word at the end of the last word is capitalized. One trailing punctuation character from the implementation's punctuation set can sit after it, so `of?` becomes `Of?`. A word fixed by the callback is left alone. This fix sees the finished token, so a small word at the end of a slash or hyphen compound is capitalized when that compound is the last word of the line.

With `small_first_last=False`, `afraid of` stays `Afraid of`.

- Input: `Small word at end is nothing to be afraid of`
- Output: `Small Word at End Is Nothing to Be Afraid Of`

`nothing to be afraid of?` becomes `Nothing to Be Afraid Of?`.

### 18. A small word after a sub-phrase marker is capitalized

After the words are joined, a lowercase small word that follows one marker and a space is capitalized. The markers are `:`, `.`, `;`, `?`, `!`, the ASCII hyphen `-`, and the dashes `–`, `‒`, `—`, and `―`. The match is case-sensitive and looks for the lowercase small-word spelling, which rule 10 has already produced. This fix still runs when `small_first_last` is false: `foo: a bar` becomes `Foo: A Bar`. A comma is not a marker: `foo, the bar` becomes `Foo, the Bar`.

- Input: `Starting Sub-Phrase With a Small Word: a Trick, Perhaps?`
- Output: `Starting Sub-Phrase With a Small Word: A Trick, Perhaps?`

The same fix turns `EPISODE 7 — THE FORCE AWAKENS` into `Episode 7 — The Force Awakens`.

## Repository Information

Repository: https://github.com/ppannuto/python-titlecase
Commit SHA: 42f43e2de55bf003b286c6f8e8d8b2d26676a167
Commit Date: 2024-04-05T22:03:59-07:00
Licence: MIT
