# python-titlecase behavior notes

Notes for the Python `titlecase` implementation in `python-titlecase/titlecase/__init__.py`. Every rule below is taken from that file. Input/output examples were checked by running this tree (version `2.4.1`) and, where noted, match `python-titlecase/titlecase/tests.py`.

The third-party `regex` package was not installed. The module therefore used its stdlib `re` fallback (`REGEX_AVAILABLE = False`). Examples below are outputs of that fallback. Rules 10, 11, and 23 record where the unread `regex` patterns differ.

## Source

- Repository path: `python-titlecase/`
- Module: `titlecase/__init__.py`
- Version in source: `2.4.1`
- Git commit: `42f43e2de55bf003b286c6f8e8d8b2d26676a167`
- Commit date: `2024-04-05T22:03:59-07:00`
- Commit subject: Merge pull request #97 from robinwhittleton/nbsp-support

## License

The MIT License (MIT).

`LICENSE.txt` begins with the line `The MIT License (MIT)` and copyright `Copyright (c) 2021 Patrick William Pannuto`. `setup.cfg` classifies the project as `License :: OSI Approved :: MIT License` and sets `license = MIT`. The module docstring points at the MIT license URL.

## How a string is processed

`titlecase(text, callback=None, small_first_last=True, preserve_blank_lines=False, normalise_space_characters=False)` walks the text in this order:

1. Split into lines (rule 1).
2. For each line, remember whether the line is already all capitals (rule 4).
3. Split the line into words on whitespace, keeping the separators (rule 2).
4. For each word, apply rules 5 through 17. The first matching rule keeps that word and skips the rest of the per-word rules.
5. Capitalize a small word at the start and end of the line when `small_first_last` is true (rules 18 and 19), unless a callback froze that word.
6. Join the words with the original separators, or with a single normal space (rule 3).
7. Capitalize a small word that opens a subphrase (rule 20). This pass does not look at the callback freeze.
8. Join the lines with `\n`.

Slash pieces and hyphen pieces are titlecased by calling `titlecase` again with `small_first_last=False`. The `Mc` remainder is titlecased by calling `titlecase` again with `small_first_last=True`. Those calls still run the subphrase pass.

## Rules

### 1. Lines and blank lines

A break is a carriage return (`\r`) or a line feed (`\n`). The pieces are always joined back with `\n`, so a carriage return in the input does not survive in the output.

By default, one or more breaks in a row are a single split. Blank lines disappear, but a break at the very start or end still produces one empty piece, so one leading or trailing `\n` can remain.

`preserve_blank_lines=True` splits on every individual `\r` or `\n` and keeps the empty pieces. A Windows `\r\n` pair is two breaks, so one physical line ending becomes two `\n` characters in the output.

Examples:

- `"this shouldn't\nget mangled"` → `"This Shouldn't\nGet Mangled"`
- `"Line number one\n\nand Line three\n"` → `"Line Number One\nAnd Line Three\n"`
- same text with `preserve_blank_lines=True` → `"Line Number One\n\nAnd Line Three\n"`
- `"\n\nLeading blank\n\n\nMulti-blank\n\n\n\n\nTrailing Blank\n\n"` → `"\nLeading Blank\nMulti-Blank\nTrailing Blank\n"`
- same text with `preserve_blank_lines=True` → `"\n\nLeading Blank\n\n\nMulti-Blank\n\n\n\n\nTrailing Blank\n\n"`
- `"a\r\nb"` → `"A\nB"`
- `"a\r\nb"` with `preserve_blank_lines=True` → `"A\n\nB"`
- `""` → `""`

### 2. Whitespace between words

Each line is split on a single whitespace character, and the separator is kept. Whitespace includes the normal space, tab, non-breaking space (`U+00A0`), and other Unicode spaces matched by `\s`. Words are not trimmed. A run of spaces stays a run of spaces. Leading spaces stay.

Examples:

- `"hello   world"` → `"Hello   World"`
- `"  hello  world"` → `"  Hello  World"`
- `"text\twith\ttabs"` → `"Text\tWith\tTabs"`
- `"text\u00a0with\u00a0nonbreaking\u00a0spaces"` → `"Text\u00a0With\u00a0Nonbreaking\u00a0Spaces"`
- `"a mix\u00a0of\tdifferent\u200aspace\u2006characters"` → `"A Mix\u00a0of\tDifferent\u200aSpace\u2006Characters"`

`of` stays lowercase in the last example because it is a small word (rule 12), not because the spaces are special.

### 3. Normalising space characters

`normalise_space_characters` defaults to `False`. When it is `True`, the original separators are thrown away and the processed words are joined with one ordinary space. The command-line interface does not expose this switch.

Examples:

- `"text\twith\ttabs"` with `normalise_space_characters=True` → `"Text With Tabs"`
- `"text\u00a0with\u00a0nonbreaking\u00a0spaces"` with `normalise_space_characters=True` → `"Text With Nonbreaking Spaces"`

### 4. All-caps line detection

Before words are handled, the line is all caps when `line.upper() == line`. Digits, punctuation, and symbols do not stop a line from counting as all caps. One lowercase letter means the line is not all caps.

This flag is per line, not per word. It is passed to the callback as `all_caps`. It decides rules 6, 11, and 15.

Examples of lines that are all caps, and what the full function returns:

- `"THIS IS ALL CAPS AND SHOULD BE ADDRESSED"` → `"This Is All Caps and Should Be Addressed"`
- `"EPISODE 7 — THE FORCE AWAKENS"` → `"Episode 7 — The Force Awakens"`
- `"AT&T IS BIG"` → `"At&t Is Big"`

`At&t` happens because rule 11 is skipped on an all-caps line and rule 15 lowercases the token before ordinary capitalization. A mixed-case line keeps `AT&T` (rule 11): `"Apple deal with AT&T falls through"` → `"Apple Deal With AT&T Falls Through"`.

### 5. Callback override

If `callback` is given, it is called as `callback(word, all_caps=all_caps)` before any other per-word rule. A truthy return value replaces the word. That word is marked immutable and is then skipped by the later per-word rules and by rules 18 and 19. An empty string or `None` is ignored, and normal rules run.

The same callback is forwarded into slash, hyphen, and `Mc` recursion.

Rule 20 still runs on the finished line, so a frozen small word can still be capitalized when it sits after subphrase punctuation.

Examples:

- `"at&t"` with a callback that returns `"AT&T"` for that word → `"AT&T"`
- `"a simple tcp and udp wrapper"` with a callback that returns `"TCP"` and `"UDP"` → `"A Simple TCP and UDP Wrapper"`
- `"the great escape"` with a callback that returns `"the"` for `the` → `"the Great Escape"`
- `"afraid of"` with a callback that returns `"OF"` for `of` → `"Afraid OF"`
- `"yes: a trick"` with a callback that returns `"a"` for `a` → `"Yes: A Trick"` (rule 20 still capitalizes `a`)
- `"hello world"` with a callback that returns `""` → `"Hello World"`
- `"SENDING UDP PACKETS OVER PPPOE WORKS GREAT"` with the abbreviation callback from rule 22 → `"Sending UDP Packets Over PPPoE Works Great"`

### 6. Uppercase initials on an all-caps line

If the line is all caps and the whole word matches the initials pattern, the word is kept unchanged.

On the stdlib `re` path the pattern is `^(?:[A-Z]\.|[A-Z]\.[A-Z])+$`. In plain terms, the word is one or more chunks of either “ASCII capital + period” or “ASCII capital + period + ASCII capital”. `A.B`, `A.B.`, `A.B.C`, `A.B.C.`, and `D.C.` match. `ABCD` and `PH.D.` do not.

This rule does not run when the line is mixed case. Lowercase initials are then left alone only when rule 10 sees an internal period.

With the `regex` package, each letter in this pattern is any Unicode uppercase letter (`\p{Uppercase_Letter}`) instead of ASCII `A-Z`. That path was not executed.

Examples:

- `"WASHINGTON, D.C. SHOULD BE FIXED BUT MIGHT BE A PROBLEM"` → `"Washington, D.C. Should Be Fixed but Might Be a Problem"`
- `"A.B.C. AND A.B.C AND D.C."` → `"A.B.C. And A.B.C and D.C."`
- `"PH.D. HOLDERS"` → `"PH.D. Holders"` (`PH.D.` is kept by rule 10, not by this rule)

### 7. Apostrophes in d, o, and l words

If the whole word matches the apostrophe pattern, it is recased and the remaining per-word rules are skipped.

The shape is:

- first character is `d`, `o`, or `l`, any case
- second character is `'` or `‘` (`U+2018` LEFT SINGLE QUOTATION MARK)
- then one or more letters
- optionally two more characters, each of which is `'` or `s` (the tested form is `'s`)

Recasing touches only the first and third characters. The rest of the word, including any `'s`, is copied as it already was. The word is not lowercased first, even on an all-caps line.

- If the first character is not a vowel (`d` or `l`), it is forced to lowercase and the third character is forced to uppercase.
- If the first character is a vowel (`o`), it is forced to uppercase and the third character is forced to uppercase.

The right single quotation mark `’` (`U+2019`) does not match. Words that merely contain an apostrophe, such as `shouldn't` or `'that's`, do not match this rule. They fall through to ordinary capitalization.

On the stdlib path, “letter” is `\w`. With the `regex` package it is `\p{Letter}`.

Examples from the test suite:

- `"l'grange l'grange l'Grange l'Grange"` → `"l'Grange l'Grange l'Grange l'Grange"`
- `"L'grange L'grange L'Grange L'Grange"` → `"l'Grange l'Grange l'Grange l'Grange"`
- `"l'GranGe"` → `"l'GranGe"`
- `"o'grange O'grange o'Grange O'Grange"` → `"O'Grange O'Grange O'Grange O'Grange"`
- `"o'grange's O'grange's o'Grange's O'Grange's"` → `"O'Grange's O'Grange's O'Grange's O'Grange's"`
- `"O'GranGe"` → `"O'GranGe"`
- `"O'Reilly should be untouched"` → `"O'Reilly Should Be Untouched"`
- `"my name is o'reilly"` → `"My Name Is O'Reilly"`

Also executed:

- `"d'artagnan"` → `"d'Artagnan"`
- `"D'ARTAGNAN"` → `"d'ARTAGNAN"`
- `"o‘reilly"` → `"O‘Reilly"` (the second character is `U+2018`)
- `"o'clock's"` → `"O'Clock's"`

### 8. Mc prefix

If the word starts with `Mc`, `mc`, or `MC`, and at least two characters follow, the prefix is rewritten with `capitalize()` (so `MC` becomes `Mc`) and the remainder is passed through `titlecase` again with `small_first_last=True`.

The remainder therefore gets the normal rules, including small-word handling and a fresh all-caps check. A small word as the entire remainder is capitalized because it is the first word of that recursive call: `mcby` → `McBy`.

`Mc`, `mc`, and `MC` alone do not match, because nothing follows the prefix. `macdonald` does not match, because the prefix is `Mac`, not `Mc`. A form such as `Mcc` does not match either: only one character follows `Mc`. It later hits the consonant-acronym rule.

Examples:

- `"Mr McTavish went to MacDonalds"` → `"Mr McTavish Went to MacDonalds"`
- `"mcdonald"` → `"McDonald"`
- `"MCDONALD"` → `"McDonald"`
- `"macdonald"` → `"Macdonald"`
- `"MACDONALD"` → `"Macdonald"`
- `"mctavish"` → `"McTavish"`
- `"foo-mcbar"` → `"Foo-McBar"`
- `"mccay-mcbut-mcdo mcdonalds/mcby"` → `"McCay-McBut-McDo McDonalds/McBy"`
- `"mcfoo-bar, MCFOO-BAR, McFoo-bar, McFoo-Bar, mcfoo-mcbar, foo-mcbar"` → `"McFoo-Bar, McFoo-Bar, McFoo-Bar, McFoo-Bar, McFoo-McBar, Foo-McBar"`
- `"mac mc MAC MC machine"` → `"Mac Mc MAC MC Machine"`
- `"Mc"` → `"Mc"`, `"mc"` → `"Mc"`, and a one-word line `"MC"` → `"Mc"` (these three do not take the prefix rule; the mixed-case line above keeps `MAC` and `MC` by rule 11)
- `"Mcc"` → `"MCC"`

### 9. Mr, Mrs, Ms, and Dr

If the whole word is `mr`, `mrs`, `ms`, or `dr` in any capitalization, the first character is uppercased and the rest is left unchanged. The word is not otherwise title-cased, so an already-uppercase remainder stays uppercase.

`mss`, `mr.`, and longer titles do not match. `Mr.` is capitalized only by rule 17. `Mss` later becomes `MSS` by rule 16.

Examples:

- `"Mr mr Mrs Ms Mss Dr dr , Mr. and Mrs. Person"` → `"Mr Mr Mrs Ms MSS Dr Dr , Mr. And Mrs. Person"`
- `"mr. smith"` → `"Mr. Smith"`
- `"mR smith"` → `"MR Smith"`
- `"MR SMITH AND MRS JONES AND MS LEE AND DR WHO"` → `"MR Smith and MRS Jones and MS Lee and DR Who"`
- `"DR SMITH"` → `"DR Smith"`

### 10. Words with an internal period

If the word contains “character, period, character” anywhere inside it, the whole word is kept exactly as written. This runs on all-caps lines too, and it runs before the all-caps lowercasing in rule 15.

On the stdlib path the character is `\w` (letter, digit, or underscore). With the `regex` package the character is a Unicode letter (`\p{Letter}`), so a period between digits or underscores would not match there. That path was not executed. The letter examples below match both pattern spellings.

`Mr.` does not match, because nothing follows the period. `http://example.com/path` matches because of `e.c` in `example.com`, and the whole token is kept, including the `//`.

Examples:

- `"this is just an example.com"` → `"This Is Just an example.com"`
- `"this is something listed on del.icio.us"` → `"This Is Something Listed on del.icio.us"`
- `"this is http://foo.com"` → `"This Is http://foo.com"`
- `"e.g. this is a.m. or p.m."` → `"e.g. This Is a.m. Or p.m."`
- `"EXAMPLE.COM SITE"` → `"EXAMPLE.COM Site"`
- `"visit d.c. now"` → `"Visit d.c. Now"`
- `"this is item.one"` → `"This Is item.one"`
- `"file_name.txt here"` → `"file_name.txt Here"`

`Or` in the `e.g.` example is rule 20: `a.m.` ends with a period, so the following small word `or` is capitalized.

### 11. Words that already contain an internal capital

If the line is not all caps, and the word matches the “uppercase elsewhere” pattern, the word is kept exactly as written.

On the stdlib path the pattern is: optional leading punctuation, then one or more ASCII letters, then one or more ASCII capitals. An uppercase letter must sit immediately after another ASCII letter. `iTunes` matches. `Q&A` does not, because `&` stands between `Q` and `A`. `O'Reilly` does not match this pattern either; rule 7 handles the `o'` shape.

This rule is skipped when the line is all caps. Those words are lowercased by rule 15 and then capitalized in the ordinary way, unless an earlier keep-rule already returned.

With the `regex` package, letters and uppercase letters are Unicode properties (`\p{Letter}` and `\p{Uppercase_Letter}`), not ASCII ranges. That path was not executed. On the stdlib path, `"iÑunes"` → `"IÑunes"`, because `Ñ` is not an ASCII `A-Z` capital, so this rule does not keep the lowercase `i`.

Examples:

- `"iTunes should be unmolested"` → `"iTunes Should Be Unmolested"`
- `"iPhone and iTunes and macOS"` → `"iPhone and iTunes and macOS"`
- `"Apple deal with AT&T falls through"` → `"Apple Deal With AT&T Falls Through"`
- `"What is AT&T's problem?"` → `"What Is AT&T's Problem?"`
- `"Mr McTavish went to MacDonalds"` → `"Mr McTavish Went to MacDonalds"` (`MacDonalds` is kept by this rule)
- `"Snakes on a Plane - The TV Edit - The Famous Line"` → `"Snakes on a Plane - The TV Edit - The Famous Line"`
- `"sending UDP packets over PPPoE works great"` → `"Sending UDP Packets Over PPPoE Works Great"`
- `"ST and St and st"` → `"ST and St and St"`
- `"IPHONE IS HERE"` → `"Iphone Is Here"`
- `"AT&T IS BIG"` → `"At&t Is Big"`

### 12. Small words

If the whole word is one of the small words, any capitalization, it is replaced with the fully lowercase form. This happens before all-caps lowercasing and before ordinary capitalization.

The list, from the `SMALL` pattern, is:

`a`, `an`, `and`, `as`, `at`, `but`, `by`, `en`, `for`, `if`, `in`, `of`, `on`, `or`, `the`, `to`, `v`, `v.`, `via`, `vs`, `vs.`

The module docstring says this list comes from the New York Times Manual of Style, plus `vs` and `v`.

The word must be the entire token. `of.` and `of?` are not small words at this step. A leading quote also prevents a match: `'by` is not the small word `by`. Words that are not in the list are capitalized normally. `be` is not in the list.

Rules 18, 19, and 20 may capitalize a small word again after this lowercasing.

Examples:

- `"this v that"` → `"This v That"`
- `"this v. that"` → `"This v. That"`
- `"this vs that"` → `"This vs That"`
- `"this vs. that"` → `"This vs. That"`
- `"this v that"` is also why `"A Title and/or String"` keeps `and` and `or` lowercase in the middle
- `"via the road"` → `"Via the Road"`
- `"en route to a win"` → `"En Route to a Win"`
- `"as if by an or but at on to for"` → `"As if by an or but at on to For"`
- `"Small word at end is nothing to be afraid of"` → `"Small Word at End Is Nothing to Be Afraid Of"` (`be` becomes `Be`)
- `"I am a cat"` → `"I Am a Cat"`

### 13. Slash-separated words

If the word contains `/` and does not contain `//`, it is split on every `/`. Each piece is passed through `titlecase` with `small_first_last=False`, then the pieces are joined with `/`.

Small words inside the pieces therefore stay lowercase unless a later line-level rule (18 or 19) capitalizes the start or end of the whole token. `//` disables this split. The word may then be kept whole by rule 10, or only its first letter is capitalized.

Examples:

- `"word/word"` → `"Word/Word"`
- `"a title and/or string"` → `"A Title and/or String"`
- `"dance with me/let’s face the music and dance"` → `"Dance With Me/Let’s Face the Music and Dance"`
- `"a/b"` → `"A/B"` (the pieces are `a` and `b`; rules 18 and 19 then capitalize both ends)
- `"and/or"` as a whole line → `"And/Or"`
- `"five-and"` at the end of `"a-b end-to-end two-not-three/three-by-four/five-and"` becomes `Five-And` for the same end-of-line reason
- `"http://example.com/path"` → `"http://example.com/path"`
- `"foo//bar baz"` → `"Foo//bar Baz"`
- `"foo/bar//baz"` → `"Foo/bar//baz"`
- `"o'melveny/o'doyle"` → `"O'Melveny/O'Doyle"`

### 14. Hyphen-separated words

If the word contains an ASCII hyphen-minus (`-`), and rule 13 did not already take it, it is split on `-`. Each piece is passed through `titlecase` with `small_first_last=False`, then joined with `-`.

Only the ASCII hyphen is a split point. An en dash, em dash, figure dash, or horizontal bar inside a token is not split. Spaced dashes are separate words and are handled by rule 20 when a small word follows them.

A small piece stays lowercase. If that piece is the end of the last word of the line, rule 19 can still capitalize it. If it is the start of the first word, rule 18 can capitalize it.

Examples:

- `"end-to-end"` in `"a-b end-to-end two-not-three/three-by-four/five-and"` → the full result is `"A-B End-to-End Two-Not-Three/Three-by-Four/Five-And"`
- `"state-of-the-art"` → `"State-of-the-Art"`
- `"well-known author"` → `"Well-Known Author"`
- `"five-and books"` → `"Five-and Books"`
- `"a-b"` → `"A-B"`
- `"state–of–the–art"` (en dashes, `U+2013`) → `"State–of–the–art"`

### 15. Lowercasing leftover words on an all-caps line

If the line is all caps and none of rules 5 through 14 kept or rewrote the word, the word is lowercased before rules 16 and 17. Small words never reach this step, because rule 12 already returned them in lowercase.

Examples:

- `"THIS IS ALL CAPS AND SHOULD BE ADDRESSED"` → `"This Is All Caps and Should Be Addressed"`
- `"YEA NO"` → `"Yea No"`
- `"FOO BAR 5TH ST"` → `"Foo Bar 5th St"`
- `"EL NIÑO A ARRIVÉ HIER"` → `"El Niño a Arrivé Hier"`

### 16. All-consonant acronyms

After rule 15, if the whole word is made only of ASCII consonants and is longer than two characters, it is replaced with the fully uppercase word.

The consonants are the ASCII letters except `a`, `e`, `i`, `o`, `u`, and `y`. `y` counts as a vowel here. Any other character, including a digit, apostrophe, accented letter, or punctuation, means the word is not an acronym under this rule. Two-letter consonant words such as `st` are not acronyms. The check is case-insensitive, then the result is uppercase.

Examples:

- `"Words with all consonants like cnn are acronyms"` → `"Words With All Consonants Like CNN Are Acronyms"`
- `"a simple tcp and udp wrapper"` → `"A Simple TCP and Udp Wrapper"` (`udp` contains `u`)
- `"why nyc html"` → `"Why Nyc HTML"` (`nyc` contains `y`; `html` does not)
- `"bb"` → `"Bb"`
- `"bbb"` → `"BBB"`
- `"cns news"` → `"CNS News"`
- `"Mss"` inside the honorific test → `"MSS"`
- `"Mcc"` → `"MCC"`
- `"cnn's report"` → `"Cnn's Report"`
- `"rhythm"` is not an acronym because of `y`. In `"HTML and CSS and NYC and rhythm and cry and st and TV and udp and tcp"` the word becomes `Rhythm`. `HTML`, `CSS`, `NYC`, `TV`, and `ST` in that sentence are kept by rule 11 because they are already uppercase on a mixed-case line. `tcp` becomes `TCP` by this rule. `cry` and `st` become `Cry` and `St`.

### 17. Ordinary first-letter capitalization

If no earlier per-word rule matched, the first letter is uppercased and every later character is left unchanged.

Leading characters from the punctuation set below are allowed before that letter, and they stay in place. The uppercasing covers the leading punctuation plus the letter, which does not change the punctuation. A word that starts with a digit or another non-punctuation, non-letter character is not changed.

The punctuation set in `PUNCT` is:

`!` `"` `“` `#` `$` `%` `&` `'` `‘` `(` `)` `*` `+` `,` `-` `–` `‒` `—` `―` `.` `/` `:` `;` `?` `@` `[` `\` `]` `_` `` ` `` `{` `|` `}` `~`

`”` (`U+201D`) and `’` (`U+2019`) are not in that set.

Examples:

- `"steve"` inside `"Q&A with steve jobs: 'that's what happens in technology'"` → the full result is `"Q&A With Steve Jobs: 'That's What Happens in Technology'"`
- `"'that's"` → `"'That's"`
- `"34th 3rd 2nd"` → `"34th 3rd 2nd"`
- `"2lmc Spool"` → `"2lmc Spool"`
- `"123 abc 4th"` → `"123 Abc 4th"`
- `"let's go"` → `"Let's Go"`
- `"let’s go"` → `"Let’s Go"` (`’` is just another character in the word)
- `"reading between the lines of steve jobs’s ‘thoughts on music’"` → `"Reading Between the Lines of Steve Jobs’s ‘Thoughts on Music’"`
- `"see q&a today"` → `"See Q&a Today"`
- `"q&a"` as a whole line → `"Q&A"` (rule 19 then capitalizes the final small word `a`)
- `"a_b"` → `"A_b"`
- `"“YOUNG AND RESTLESS”"` → `"“Young and Restless”"`
- `"'QUOTE' A GREAT"` → `"'Quote' a Great"`

### 18. Small word at the beginning

When `small_first_last` is true (the default) and the first word was not frozen by a callback, a small word at the start of that word is capitalized.

Optional punctuation from the set in rule 17 may sit in front of the small word. The small-word portion is replaced with `capitalize()`, which uppercases its first character and lowercases the rest of that portion.

`small_first_last=False` skips this step. Slash and hyphen pieces use `False`. The `Mc` remainder uses `True`.

Examples:

- `"a thing"` → `"A Thing"`
- `"'by the Way, small word at the start but within quotes.'"` → `"'By the Way, Small Word at the Start but Within Quotes.'"`
- `"a-b"` → `"A-B"`
- `"a tale of two cities"` with `small_first_last=False` → `"a Tale of Two Cities"`
- `"of mice and men"` with `small_first_last=False` → `"of Mice and Men"`

### 19. Small word at the end

When `small_first_last` is true and the last word was not frozen by a callback, a small word at the end of that word is capitalized with `capitalize()`.

The match is a word boundary, then a small word, then at most one character from the punctuation set, and then the end of the word. Two trailing punctuation characters mean this rule does not match. `capitalize()` lowercases the rest of the matched text, so `OF.` becomes `Of.`.

This sees the whole last token, so it can capitalize a small word at the end of a hyphenated or slash-separated token.

Examples:

- `"Small word at end is nothing to be afraid of"` → `"Small Word at End Is Nothing to Be Afraid Of"`
- `'"Nothing to Be Afraid of?"'` → `'"Nothing to Be Afraid Of?"'`
- `'"Nothing to be Afraid Of?"'` → `'"Nothing to Be Afraid Of?"'`
- `"NOTHING TO BE AFRAID OF?"` → `"Nothing to Be Afraid Of?"`
- `"afraid OF."` → `"Afraid Of."`
- `"end OF?"` → `"End Of?"`
- `"end OF?!"` → `"End OF?!"`
- `"afraid OF!?"` → `"Afraid OF!?"`
- `"nothing to be afraid of"` with `small_first_last=False` → `"Nothing to Be Afraid of"`
- `"q&a"` → `"Q&A"`, while `"see q&a today"` → `"See Q&a Today"`
- the last token of `"a-b end-to-end two-not-three/three-by-four/five-and"` ends as `Five-And`

### 20. Small word after subphrase punctuation

After the line is joined, a small word is capitalized when it comes immediately after one specific punctuation character and a space.

The punctuation character is one of `:` `.` `;` `?` `!` `-` `–` (`U+2013` EN DASH) `‒` (`U+2012` FIGURE DASH) `—` (`U+2014` EM DASH) `―` (`U+2015` HORIZONTAL BAR).

The small word is replaced with `capitalize()`. This pass always runs, including when `small_first_last` is `False`, and including on text a callback already returned. A small word inside quotes does not match, because the quote sits between the space and the word. That quoted word is usually capitalized earlier by rule 17.

`set_small_word_list` rebuilds this pattern without the hyphen and the four wide dashes. See rule 21.

Examples:

- `"Starting Sub-Phrase With a Small Word: a Trick, Perhaps?"` → `"Starting Sub-Phrase With a Small Word: A Trick, Perhaps?"`
- `"Starting a Hyphen Delimited Sub-Phrase With a Small Word - a Trick, Perhaps?"` → `"Starting a Hyphen Delimited Sub-Phrase With a Small Word - A Trick, Perhaps?"`
- `"Starting an Em Dash Delimited Sub-Phrase With a Small Word — a Trick, Perhaps?"` → `"Starting an Em Dash Delimited Sub-Phrase With a Small Word — A Trick, Perhaps?"`
- `"Snakes on a Plane — The TV Edit — The Famous Line"` → `"Snakes on a Plane — The TV Edit — The Famous Line"`
- `"word – a trick"` → `"Word – A Trick"`
- `"word ‒ a trick"` → `"Word ‒ A Trick"`
- `"word ― a trick"` → `"Word ― A Trick"`
- `"yes? a trick"` → `"Yes? A Trick"`
- `"yes! a trick"` → `"Yes! A Trick"`
- `"yes; a trick"` → `"Yes; A Trick"`
- `"yes. a trick"` → `"Yes. A Trick"`
- `"yes: a trick"` with `small_first_last=False` → `"Yes: A Trick"`
- `"Sub-Phrase With a Small Word in Quotes: 'a Trick, Perhaps?'"` → `"Sub-Phrase With a Small Word in Quotes: 'A Trick, Perhaps?'"`
- `"v. vs. via v vs"` → `"V. Vs. Via v Vs"` (`vs.` and `via` follow a period and a space; the lone `v` does not)
- `"Mr mr Mrs Ms Mss Dr dr , Mr. and Mrs. Person"` → `"Mr Mr Mrs Ms MSS Dr Dr , Mr. And Mrs. Person"`

### 21. Custom small-word list

`set_small_word_list(small)` replaces the global patterns used by rules 12, 18, 19, and 20. The argument is the inside of a regular expression, using `|` between choices, not a Python list. The default argument is the `SMALL` string from rule 12.

The rebuilt subphrase pattern is only `:` `.` `;` `?` `!` plus a space. It does not include the ASCII hyphen or the four wide dashes, even if the caller passes the original small-word string. Calling `set_small_word_list` therefore cannot restore the dash half of rule 20. The change is process-global.

`titlecase/tests.py` contains `TestSmallWordList`, and that test is skipped with a note that moving to `unittest` exposed a global-state bug. The outputs below were executed directly.

Examples, after `set_small_word_list("a|an|the|with")`:

- `'playing the game "words with friends"'` → `'Playing the Game "Words with Friends"'`
- `"words with friends"` → `"Words with Friends"`
- `"Start — a trick"` → `"Start — a Trick"` (the em dash no longer triggers rule 20)
- `"Start: a trick"` → `"Start: A Trick"` (the colon still does)

Before that call, the same first string is `'Playing the Game "Words With Friends"'`, and `"Start — a trick"` is `"Start — A Trick"`.

### 22. Abbreviation word list

`create_wordlist_filter_from_file(file_path)` returns a callback for rule 5.

- `None`, or a path that is not a file: the callback returns `None`. Normal rules run. A missing file is not an error.
- Otherwise each non-empty line is stripped and stored. Lookup uses the uppercased word. The returned spelling is the text from the file, not a generated title case. Later duplicate lines replace earlier ones for the same uppercased key.

The callback receives one whitespace-separated word, so a file line that contains a space cannot match a normal word.

`titlecase()` does not open a word list by itself. The command-line `cmd()` always installs this callback. It uses `-w` / `--wordlist` when given, and otherwise `~/.titlecase.txt`.

Examples, with a file containing `UDP` and `PPPoE`:

- `"sending UDP packets over PPPoE works great"` → `"Sending UDP Packets Over PPPoE Works Great"`
- `"sending udp packets over pppoe works great"` → `"Sending UDP Packets Over PPPoE Works Great"`
- `"SENDING UDP PACKETS OVER PPPOE WORKS GREAT"` → `"Sending UDP Packets Over PPPoE Works Great"`

Without that callback, the all-caps sentence becomes `"Sending Udp Packets Over Pppoe Works Great"`. `UDP` contains `u`, so rule 16 does not treat it as an acronym after rule 15 lowercases it.

### 23. Unicode letters and the two regular-expression engines

Python’s own `str.upper`, `str.lower`, and `str.capitalize` do the case changes. Accented letters follow those methods.

The module first tries `import regex`. If that works, word patterns use Unicode properties such as `\p{Letter}` and `\p{Uppercase_Letter}`. If it fails, the module imports stdlib `re` and uses `\w`, `[a-zA-Z]`, and `[A-Z]` as written in the `else` branch of `__init__.py`. Both branches exist in the source. This environment took the `else` branch, and the project’s unit tests passed on that branch (one skipped test, `TestSmallWordList`).

Examples executed on the stdlib path:

- `"EL NIÑO A ARRIVÉ HIER"` → `"El Niño a Arrivé Hier"`
- `"ÝÆ ÑØ"` → `"Ýæ Ñø"`
- `"ýæ ñø"` → `"Ýæ Ñø"`
- `"THE CASE OF X ≤ 7"` → `"The Case of X ≤ 7"`
- `"the case of X ≤ 7"` → `"The Case of X ≤ 7"`
- `"iÑunes"` → `"IÑunes"`

`≤` is left unchanged because it is not a letter and not part of a matched word pattern.

## Command-line options

`cmd()` in the same file is the command-line wrapper. It does not add casing rules of its own. It calls `titlecase` with:

- the positional arguments joined by one space, or the whole input file if there are no positional arguments
- `-f` / `--input-file`, where `-` means standard input
- `-o` / `--output-file`, where `-` means standard output
- the abbreviation callback from rule 22 (`-w` / `--wordlist`, otherwise `~/.titlecase.txt`)
- `preserve_blank_lines` from `--preserve-blank-lines`

`small_first_last` and `normalise_space_characters` are not command-line switches.

## Unclear behavior that needs a manual check

- The `regex` package branch was not run. Its patterns are in the `if REGEX_AVAILABLE` branch. They treat letters and uppercase letters as Unicode properties. The stdlib branch uses `\w` and ASCII `[A-Z]` / `[a-zA-Z]`. A concrete difference already visible from the source, and checked only on stdlib `re`, is `"iÑunes"` → `"IÑunes"`. With `\p{Uppercase_Letter}`, rule 11 may keep `iÑunes` unchanged. The same gap applies to non-ASCII initials in rule 6, and to whether rule 10 matches a period between digits or underscores (`\w` versus `\p{Letter}`).
- Rule 7’s optional ending is any two characters from the set `'s`, not only the letters `'s`. The executed examples cover `'s` (`o'clock's`, `o'grange's`). Outputs for the other pairs (`ss`, `s'`, `''`) were not run.
- `TestSmallWordList` is skipped in the repository. The comment above it says converting the tests to `unittest` exposed a global-state bug, and that `set_small_word_list` does not rebuild the original subphrase expression. Direct calls match that description for dashes (rule 21). Whether any further global interaction was intended is not settled by a passing test.
