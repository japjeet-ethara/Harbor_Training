# Port `titlecase()` to Go

Implement the Python `titlecase()` string transform from python-titlecase 2.4.1 in Go. Exact output equivalence applies to the supported string API and the behaviour documented below: for those inputs, the Go function must return the same Unicode string, code point for code point. Match spaces, punctuation, quotes, line breaks, and casing exactly. That equivalence does not cover the excluded bytes API.

The reference implementation is the bundled package:

- `titlecase/__init__.py` (`titlecase`, version `2.4.1`)
- `titlecase/tests.py`
- `README.rst`

Read those files. Do not modify them. Do not shell out to Python to produce the answer. Implement the rules below in Go.

This document is only the behavior contract. It is not a Go implementation.

## Scope

Implement the library function and the abbreviation-file callback helper. Both are covered by the active unit tests.

Parameters that change output:

- `text`
- `callback`
- `small_first_last` (default true)
- `preserve_blank_lines` (default false)
- `normalise_space_characters` (default false)

Keep the British spelling `normalise`.

Out of scope:

- The command-line wrapper `cmd()` (`titlecase` console script, `-f`, `-o`, `-w`, `~/.titlecase.txt`). No active unit test calls it.
- `set_small_word_list`. Its only unit test is skipped (`FIXME: Converting to unittest exposed a bug`). The helper also compiles a different subphrase expression than the one `titlecase()` uses on startup. Leave the default subphrase rules below intact.
- Logging.
- A bytes API. Tests pass Unicode strings (`str`). `ImmutableBytes` exists in the source and is not exercised by tests.

## Task API

Create a Go module named `titlecase` in a new directory `go-titlecase` next to the bundled `python-titlecase` tree. In the task container the Python tree is at `/workspace/repo` and the module should be `/workspace/titlecase`.

Target the Go toolchain already in the image (Go 1.23).

Export:

- `Titlecase(text string, opts *Options) string`
- `DefaultOptions() Options`
- `NewWordlistCallback(path string) func(word string, allCaps bool) string`

`opts == nil` means `DefaultOptions()`.

`Options` fields:

- `Callback func(word string, allCaps bool) string`
- `SmallFirstLast bool`
- `PreserveBlankLines bool`
- `NormaliseSpaceCharacters bool`

`DefaultOptions()` sets `SmallFirstLast` to true and the other fields to false / nil. A Go zero `Options` value has `SmallFirstLast == false`, which is not the Python default. Callers who fill in a struct themselves must set `SmallFirstLast` explicitly. Recursive calls must pass the flag value given in the rules below, not the outer call's flag.

`Callback` return value: a non-empty string means "this token is finished." An empty string means "not handled," including when the callback is nil. This mirrors Python `if new_word:`. A callback cannot force an empty token by returning `""`; processing continues with the original token. The Python callback receives `all_caps` as a keyword argument; the Go callback receives that same line-level boolean.

`NewWordlistCallback` is the Go form of `create_wordlist_filter_from_file`:

- A nil-equivalent path is the empty string. A path that is not an existing file returns a callback that always returns `""`. The Python function logs and does not raise in those two cases.
- Otherwise read the file as text, one entry per line. Skip lines that are empty after `strip` (leading and trailing Unicode whitespace, matching Python `str.strip`).
- Map `upper(stripped line)` to the stripped line itself. If the same uppercased key appears twice, the later line wins.
- For a token, return the stored spelling when `upper(token)` is a key, otherwise `""`.
- The callback ignores `allCaps`.
- The active test writes `UDP` and `PPPoE` and expects those exact spellings. Non-ASCII abbreviation files, file encoding, and unreadable paths are not specified by the tests. See Ambiguities.

## Which regex dialect to follow

`titlecase()` prefers the third-party `regex` module and falls back to the stdlib `re` module. CI runs the same tests both ways, and the published tests pass on both.

Implement the `regex`-module patterns (Unicode letter properties). Do not implement the ASCII fallback. The fallback differs for inputs the tests never give; those differences are listed under Ambiguities. The patterns in this document are the `regex` versions.

Case flags below are Unicode case-insensitivity, written as `IGNORECASE`. Patterns without that flag are case-sensitive.

## Constants

Small words, case-insensitive, entire token only:

```text
a | an | and | as | at | but | by | en | for | if | in | of | on | or | the | to | v | v. | via | vs | vs.
```

The source expression is:

```text
a|an|and|as|at|but|by|en|for|if|in|of|on|or|the|to|v\.?|via|vs\.?
```

`v\.?` is `v` with an optional period. `vs\.?` is `vs` with an optional period. `via` is the whole word `via`. Matching is anchored at both ends, so `v` does not match `via`.

There is no `is`, `be`, `with`, `from`, `into`, `onto`, `over`, `nor`, `not`, or `yet` in the default list. `with` appears only in the skipped custom-list test. Do not treat it as small by default.

Punctuation class `PUNCT`, used inside character classes:

```text
! " “ # $ % & ' ‘ ( ) * + , - – ‒ — ― . / : ; ? @ [ \ ] _ ` { | } ~
```

Code points that are easy to miss:

- `"` U+0022 and `“` U+201C
- `'` U+0027 and `‘` U+2018
- `-` U+002D HYPHEN-MINUS
- `–` U+2013 EN DASH
- `‒` U+2012 FIGURE DASH
- `—` U+2014 EM DASH
- `―` U+2015 HORIZONTAL BAR
- `\` U+005C and `]` U+005D
- `` ` `` U+0060

These characters occur in the tests and are not in `PUNCT`:

- `’` U+2019 RIGHT SINGLE QUOTATION MARK (`let’s`, `jobs’s`, `music’`)
- `”` U+201D RIGHT DOUBLE QUOTATION MARK (`RESTLESS”`)
- `≤` and digits

`’` is not an apostrophe trigger and is not leading punctuation for the capitalizer.

Derived patterns, copied from the startup path (this is the path the active tests use):

```text
SMALL_WORDS   ^(<small>)$                                          IGNORECASE
SMALL_FIRST   ^([<PUNCT>]*)(<small>)\b                             IGNORECASE
SMALL_LAST    \b(<small>)[<PUNCT>]?$                               IGNORECASE
SUBPHRASE     ([:.;?!\-–‒—―][ ])(<small>)                          case-sensitive, no trailing \b
MAC_MC        ^([Mm]c|MC)(\w.+)                                    case-sensitive
MR_MRS_MS_DR  ^((m((rs?)|s))|Dr)$                                  IGNORECASE
INLINE_PERIOD [\p{Letter}][.]\p{Letter}                            IGNORECASE, search anywhere
UC_ELSEWHERE  [<PUNCT>]*?\p{Letter}+\p{Uppercase_Letter}+?         case-sensitive, anchored at start
CAPFIRST      ^[<PUNCT>]*?(\p{Letter})                             case-sensitive
APOS_SECOND   ^[dol]['‘]\p{Letter}+(?:['s]{2})?$                   IGNORECASE, entire token
UC_INITIALS   ^(?:\p{Uppercase_Letter}\.|\p{Uppercase_Letter}\.\p{Uppercase_Letter})+$
```

`<small>` is the small-word expression above. `\b` is a Unicode word boundary. `\w` is a Unicode word character. `\p{Letter}` and `\p{Uppercase_Letter}` are Unicode properties. `.` in `MAC_MC` does not match a newline.

`SUBPHRASE` delimiters are only `: . ; ? ! - – ‒ — ―` followed by one ordinary space (U+0020). Comma, slash, quotes, parentheses, and en-dash-with-no-space are not subphrase delimiters. The small-word alternative is not followed by a word boundary.

`UC_INITIALS` is an entire-token repeat of either "one uppercase letter plus a period" or "uppercase letter, period, uppercase letter".

## Case operations

Use the same operations the Python tests rely on:

- `upper(s)` / `lower(s)`: Unicode case mapping of the whole string.
- `capitalize(s)`: uppercase the first character and lowercase the remainder. Python `str.capitalize` does this. `"vs.".capitalize()` is `"Vs."`. `"v.".capitalize()` is `"V."`.
- A line is all-caps when `upper(line) == line`. Punctuation, digits, and symbols that do not change under uppercase still leave the line all-caps. Each line has its own flag. The flag is computed on the raw line, before token edits. Every recursive `Titlecase` call recalculates `all_caps` from its own argument (`upper(argument) == argument`). Recursive calls for `Mc`, slash, and hyphen can have a different `all_caps` value from the parent line. The callback on those pieces sees the recalculated flag, not the parent line's flag.
- Acronym uppercasing uses `upper` of the whole token, not `capitalize`.

The published tests only require case mapping for ASCII plus `ñ é ý æ ø Ñ É Ý Æ Ø` (one code point to one code point). See Ambiguities for `ß`, ligatures, and final sigma.

Vowel sets differ and must stay different:

- Apostrophe rule vowels: `a e i o u A E I O U`. `y` is not a vowel here.
- Acronym vowels: `a e i o u y`. A token is an all-consonant acronym only when every character is in `bcdfghjklmnpqrstvwxz` (ASCII, case-insensitive) and the length is greater than 2. Accented letters, digits, and punctuation disqualify the token.

Length is the number of Unicode code points.

## Line breaking

If `preserve_blank_lines` is false, split on one or more CR or LF characters (`[\r\n]+`). If it is true, split on each individual CR or LF (`[\r\n]`). The delimiters are not kept. Join the processed lines with `\n` (U+000A) only.

Consequences locked by tests:

```text
""                                      -> ""
"this shouldn't\nget mangled"           -> "This Shouldn't\nGet Mangled"
"Line number one\n\nand Line three\n"   -> "Line Number One\nAnd Line Three\n"
  with preserve_blank_lines             -> "Line Number One\n\nAnd Line Three\n"
"\n\nLeading blank\n\n\nMulti-blank\n\n\n\n\nTrailing Blank\n\n"
                                        -> "\nLeading Blank\nMulti-Blank\nTrailing Blank\n"
  with preserve_blank_lines             -> "\n\nLeading Blank\n\n\nMulti-Blank\n\n\n\n\nTrailing Blank\n\n"
```

Leading and trailing newline runs still produce the empty segments that `split` produces, including one trailing `\n` when the input ends in a newline. Collapsing applies only in the default mode. `and` at the start of a later line is capitalized because first-word handling is per line.

CRLF behavior is source-defined and not present in the tests. See Ambiguities.

## Tokens and whitespace

On each line, split on every single whitespace character, keeping the separators: pattern `(\s)`. `\s` is Unicode whitespace, one code point at a time, not a run. CR and LF are already removed by the line split.

Even pieces are tokens. Odd pieces are the original whitespace characters between them. A leading or trailing separator produces an empty token, and so does each extra whitespace character inside a run. Empty tokens stay empty unless a callback replaces them with a non-empty string.

Rejoin:

- If `normalise_space_characters` is false, put each original whitespace character back between the processed tokens, including empty tokens. Runs such as NBSP, tab, and hair space stay as they were.
- If it is true, join the processed token list with U+0020. Empty tokens remain in the list, so a run of N whitespace characters still yields N spaces. The original whitespace characters are discarded.

Locked by tests (middle dot in the source file is U+00A0, and the long example also uses U+200A and U+2006):

```text
"text\twith\ttabs"                         -> "Text\tWith\tTabs"
  with normalise_space_characters          -> "Text With Tabs"
"text\u00a0with\u00a0nonbreaking\u00a0spaces"
                                           -> "Text\u00a0With\u00a0Nonbreaking\u00a0Spaces"
  with normalise_space_characters          -> "Text With Nonbreaking Spaces"
"a mix\u00a0of\tdifferent\u200aspace\u2006characters"
                                           -> "A Mix\u00a0of\tDifferent\u200aSpace\u2006Characters"
```

`of` stays lowercase because it is a small word. The other words are capitalized. The separator characters are unchanged in the default mode.

Apply the subphrase rule only after the line is joined, and apply it to that joined line.

## Per-token order

Process tokens from left to right. The first matching rule wins. Later rules do not see that token.

1. Callback, if set. Call it with the raw token and the line's all-caps flag. The raw token still has attached punctuation (`jobs:`, `'by`, `of?"`, `D.C.`). If the result is non-empty, keep it and mark it immutable. Skip rules 2–12 for this token.

2. If the line is all-caps and the token matches `UC_INITIALS`, keep the token unchanged.

3. If the token matches `APOS_SECOND`, rewrite it and keep the result (see below).

4. If the token matches `MAC_MC`, rewrite it and keep the result (see below).

5. If the token matches `MR_MRS_MS_DR`, set it to `upper(first character) + the rest unchanged`.

6. If `INLINE_PERIOD` matches anywhere in the token, or the line is not all-caps and `UC_ELSEWHERE` matches at the start, keep the token unchanged. Inline periods are kept even on all-caps lines. Internal capitals are kept only when the line is not all-caps.

7. If `SMALL_WORDS` matches, append `lower(token)`.

8. If the token contains `/` and does not contain `//`, split on `/`, run `Titlecase` on each piece with the same callback, `SmallFirstLast` false, and both blank-line and space-normalise flags false, then join the pieces with `/`.

9. If the token contains `-` (U+002D only), split on `-`, recurse the same way as slash, and join with `-`. En dash, em dash, figure dash, and horizontal bar do not split tokens.

10. If the line is all-caps, set the token to `lower(token)`.

11. If the token is an all-consonant acronym (set and length above), append `upper(token)`.

12. Otherwise apply `CAPFIRST`: if the token matches, replace that match with `upper(match)`. The match is any leading `PUNCT` plus the first letter. The rest of the token is unchanged. If it does not match, the token stays as it is. Digits are not in `PUNCT` and are not letters, so `34th`, `3rd`, `2nd`, and `5th` stay as they are. On an all-caps line, step 10 has already lowercased `5TH` to `5th`.

After every token on the line:

- If `SmallFirstLast` is true and the token list is non-empty:
  - If the first token is not immutable, apply `SMALL_FIRST`. Replace the match with `group1 + capitalize(group2)`. `group1` is the leading punctuation, possibly empty.
  - If the last token is not immutable, apply `SMALL_LAST` to that token (it may be the same token as the first). Replace the match with `capitalize(entire match)`.
- Immutability applies only to those two substitutions, and only to the token object produced by the callback in this call. A string returned from a recursive `Titlecase` is not immutable.
- Then apply `SUBPHRASE` to the joined line, repeatedly, left to right, non-overlapping. Replace each match with `group1 + capitalize(group2)`. This pass still sees words that the callback marked immutable, because it runs on the finished string.

`SmallFirstLast` false skips the first/last substitutions. The subphrase pass still runs. Slash pieces, hyphen pieces, and the portion after an `Mc` prefix are separate `Titlecase` calls and run their own subphrase pass on that piece.

## Apostrophe tokens (`APOS_SECOND`)

The whole token must match. The first character is `d`, `o`, or `l` in either case. The second character is `'` U+0027 or `‘` U+2018. Then one or more letters. Then, optionally, exactly two characters that are each `'` or `s` (`'s`, `s'`, `''`, or `ss`).

Rewrite:

- If the first character is not in `aeiouAEIOU`, lowercase it. Otherwise uppercase it.
- Leave the second character as it is.
- Uppercase the third character.
- Leave every following character exactly as it was, including capitals and a trailing `'s`.

Locked examples:

```text
"O'Reilly should be untouched"     -> "O'Reilly Should Be Untouched"
"my name is o'reilly"              -> "My Name Is O'Reilly"
"l'grange l'grange l'Grange l'Grange" -> "l'Grange l'Grange l'Grange l'Grange"
"L'grange L'grange L'Grange L'Grange" -> "l'Grange l'Grange l'Grange l'Grange"
"l'GranGe"                         -> "l'GranGe"
"o'grange O'grange o'Grange O'Grange" -> "O'Grange O'Grange O'Grange O'Grange"
"o'grange's O'grange's o'Grange's O'Grange's" -> "O'Grange's O'Grange's O'Grange's O'Grange's"
"O'GranGe"                         -> "O'GranGe"
"o'melveny/o'doyle ..." (five casings in the test) -> each piece "O'Melveny/O'Doyle"
```

The slash token does not itself match `APOS_SECOND`. Rule 8 splits it, and each piece matches. `shouldn’t` does not match, because the apostrophe is not the second character; `CAPFIRST` produces `Shouldn't`.

`’` U+2019 does not trigger this rule. `jobs’s` becomes `Jobs’s` through `CAPFIRST`. `let’s` becomes `Let’s`.

## `Mc` tokens (`MAC_MC`)

The prefix must be exactly `Mc`, `mc`, or `MC`. `mC` does not match. The remainder must be at least two characters and must start with a word character. The rest of the remainder may contain hyphens and slashes.

Result: `capitalize(prefix) + Titlecase(remainder, same callback, SmallFirstLast true)`. `capitalize` of `Mc`, `mc`, and `MC` is `Mc`. The recursive call uses default blank-line and space flags (both false) and may itself split on `/` or `-` or find another `Mc` prefix.

This rule runs before slash and hyphen splitting. Locked examples:

```text
"Mr McTavish went to MacDonalds" -> "Mr McTavish Went to MacDonalds"
"mac mc MAC MC machine"          -> "Mac Mc MAC MC Machine"
"mccay-mcbut-mcdo mcdonalds/mcby" -> "McCay-McBut-McDo McDonalds/McBy"
"oblon, spivak, mcclelland, maier & neustadt" -> "Oblon, Spivak, McClelland, Maier & Neustadt"
"Mcoblon, spivak, mcclelland, mcmaier, & mcneustadt" -> "McOblon, Spivak, McClelland, McMaier, & McNeustadt"
"mcfoo-bar, MCFOO-BAR, McFoo-bar, McFoo-Bar, mcfoo-mcbar, foo-mcbar"
    -> "McFoo-Bar, McFoo-Bar, McFoo-Bar, McFoo-Bar, McFoo-McBar, Foo-McBar"
```

`MacDonalds` is preserved on a mixed-case line by `UC_ELSEWHERE` (an uppercase letter after a letter). There is no `Mac` prefix rule. `mac` becomes `Mac` through `CAPFIRST`. `mc` and `MC` are too short for `MAC_MC`. On a mixed-case line, `MC` and `MAC` are preserved by `UC_ELSEWHERE`. On an all-caps line they would go through the later rules; the tests do not put `MACDONALDS` alone on an all-caps line.

The source comments say the `Mc` examples are contrived and might change later. Match the current expected strings above.

## Honorifics (`MR_MRS_MS_DR`)

Entire token, case-insensitive: `mr`, `mrs`, `ms`, or `dr`. Periods are not included. `mss` is not an honorific.

Only the first character is forced uppercase. The remaining characters stay as they were. `dr` becomes `Dr`. `DR` stays `DR`. `MRS` stays `MRS`. The tests cover `Mr`, `mr`, `Mrs`, `Ms`, `Dr`, and `dr`, and they do not cover `DR` or `MRS`. Follow the "first character only" rule anyway.

`Mss` fails the honorific expression, then fails the earlier preserve rules, then matches the consonant-acronym rule (length 3) and becomes `MSS`.

```text
"Mr mr Mrs Ms Mss Dr dr , Mr. and Mrs. Person"
    -> "Mr Mr Mrs Ms MSS Dr Dr , Mr. And Mrs. Person"
```

`Mr.` is an ordinary token. The period plus the following space is a subphrase delimiter, so the following small word `and` becomes `And`.

## Slashes, hyphens, and subphrases

Slash splitting requires a `/` and rejects the token when `//` is present. Hyphen splitting is U+002D only. Both recursions use `SmallFirstLast` false, so a small word at the end of a piece stays small until the outer token is fixed by `SMALL_LAST` or by `SUBPHRASE`.

Locked examples:

```text
"word/word" -> "Word/Word"
"a title and/or string" -> "A Title and/or String"
"dance with me/let’s face the music and dance"
    -> "Dance With Me/Let’s Face the Music and Dance"
"a-b end-to-end two-not-three/three-by-four/five-and"
    -> "A-B End-to-End Two-Not-Three/Three-by-Four/Five-And"
"this is http://foo.com" -> "This Is http://foo.com"
```

`and/or` stays lowercase because both pieces are small words and the token is neither first nor last. `a-b` becomes `A-B` because the outer first/last passes capitalize both ends. `five-and` becomes `Five-And` because it is the end of the last token. `by` and `to` sit in the middle of their tokens and stay lowercase. `not` is not a small word, so it becomes `Not`. `http://foo.com` matches `INLINE_PERIOD` (`o.c` is letter-dot-letter) and is kept before the slash rule runs. The `//` guard is therefore not what this particular test demonstrates.

Subphrase examples (small word after the delimiter is capitalized; other small words stay small):

```text
"Starting Sub-Phrase With a Small Word: a Trick, Perhaps?"
    -> "Starting Sub-Phrase With a Small Word: A Trick, Perhaps?"
"Sub-Phrase With a Small Word in Quotes: 'a Trick, Perhaps?'"
    -> "Sub-Phrase With a Small Word in Quotes: 'A Trick, Perhaps?'"
"sub-phrase with a small word in quotes: \"a trick, perhaps?\""
    -> "Sub-Phrase With a Small Word in Quotes: \"A Trick, Perhaps?\""
"Starting a Hyphen Delimited Sub-Phrase With a Small Word - a Trick, Perhaps?"
    -> "Starting a Hyphen Delimited Sub-Phrase With a Small Word - A Trick, Perhaps?"
"Hyphen Delimited Sub-Phrase With a Small Word in Quotes - 'a Trick, Perhaps?'"
    -> "Hyphen Delimited Sub-Phrase With a Small Word in Quotes - 'A Trick, Perhaps?'"
"Hyphen Delimited sub-phrase with a small word in quotes - \"a trick, perhaps?\""
    -> "Hyphen Delimited Sub-Phrase With a Small Word in Quotes - \"A Trick, Perhaps?\""
"Snakes on a Plane - The TV Edit - The Famous Line"
    -> "Snakes on a Plane - The TV Edit - The Famous Line"
"Starting an Em Dash Delimited Sub-Phrase With a Small Word — a Trick, Perhaps?"
    -> "Starting an Em Dash Delimited Sub-Phrase With a Small Word — A Trick, Perhaps?"
"Em Dash Delimited Sub-Phrase With a Small Word in Quotes — 'a Trick, Perhaps?'"
    -> "Em Dash Delimited Sub-Phrase With a Small Word in Quotes — 'A Trick, Perhaps?'"
"Em Dash Delimited sub-phrase with a small word in quotes — \"a trick, perhaps?\""
    -> "Em Dash Delimited Sub-Phrase With a Small Word in Quotes — \"A Trick, Perhaps?\""
"Snakes on a Plane — The TV Edit — The Famous Line"
    -> "Snakes on a Plane — The TV Edit — The Famous Line"
"generalissimo francisco franco: still dead; kieren McCarthy: still a jackass"
    -> "Generalissimo Francisco Franco: Still Dead; Kieren McCarthy: Still a Jackass"
```

`The` after ` - ` or ` — ` is a small word that was lowercased, then `SUBPHRASE` capitalizes it. `on` and `a` have no such delimiter and stay lowercase. `TV` is preserved by `UC_ELSEWHERE` because the line is not all-caps. The quote character before `a` is not a subphrase delimiter; the `:` or `-` or `—` plus the space is the delimiter, and the quote is leading punctuation on the following token, which `CAPFIRST` / the already-lowercased small word then capitalizes.

Figure dash U+2012 and horizontal bar U+2015 are in the same classes as the tested dashes. No test string contains them.

## Small words at the ends

A small word that is the whole first token is lowercased by rule 7 and then capitalized by `SMALL_FIRST`. A small word that is the whole last token is capitalized by `SMALL_LAST`. A small word in the middle stays lowercase.

```text
"a thing" -> "A Thing"
"this v that" -> "This v That"
"this v. that" -> "This v. That"
"this vs that" -> "This vs That"
"this vs. that" -> "This vs. That"
"Small word at end is nothing to be afraid of"
    -> "Small Word at End Is Nothing to Be Afraid Of"
"'by the Way, small word at the start but within quotes.'"
    -> "'By the Way, Small Word at the Start but Within Quotes.'"
"\"Nothing to Be Afraid of?\"" -> "\"Nothing to Be Afraid Of?\""
"\"Nothing to be Afraid Of?\"" -> "\"Nothing to Be Afraid Of?\""
```

`is` and `be` are not small, so they become `Is` and `Be`. `but`, `at`, `the`, and `to` are small. The first token `'by` does not match `SMALL_WORDS` because of the quote; `CAPFIRST` uppercases the leading quote plus `b`, producing `'By`.

`of?"` does not match `SMALL_WORDS`. `CAPFIRST` produces `Of?"`. `SMALL_LAST` allows at most one trailing punctuation character, so it is not what capitalizes `of?"`.

`SMALL_FIRST` has a trailing word boundary, so a first token `andromeda` is capitalized as a normal word, not as the small word `a` or `and`.

## Internal capitals, initials, domains, and acronyms

On a mixed-case line, a token with an uppercase letter after a letter is kept (`UC_ELSEWHERE`). Leading `PUNCT` is allowed. This is why these stay as written:

```text
"What is AT&T's problem?" -> "What Is AT&T's Problem?"
"Apple deal with AT&T falls through" -> "Apple Deal With AT&T Falls Through"
"Q&A with steve jobs: 'that's what happens in technology'"
    -> "Q&A With Steve Jobs: 'That's What Happens in Technology'"
"iTunes should be unmolested" -> "iTunes Should Be Unmolested"
"this is just an example.com" -> "This Is Just an example.com"
"this is something listed on del.icio.us" -> "This Is Something Listed on del.icio.us"
"The SEC's Apple probe: what you need to know"
    -> "The SEC's Apple Probe: What You Need to Know"
"reading between the lines of steve jobs’s ‘thoughts on music’"
    -> "Reading Between the Lines of Steve Jobs’s ‘Thoughts on Music’"
"seriously, ‘repair permissions’ is voodoo"
    -> "Seriously, ‘Repair Permissions’ Is Voodoo"
```

`example.com` and `del.icio.us` match `INLINE_PERIOD` and are kept in their original case. `‘` U+2018 is leading punctuation, so `‘thoughts` becomes `‘Thoughts`. The closing `’` U+2019 stays on `Music’`.

All-caps lines are lowercased only after the preserve rules. Initials that match `UC_INITIALS` are kept. `D.C.` matches as `D.` plus `C.`.

```text
"WASHINGTON, D.C. SHOULD BE FIXED BUT MIGHT BE A PROBLEM"
    -> "Washington, D.C. Should Be Fixed but Might Be a Problem"
"THIS IS ALL CAPS AND SHOULD BE ADDRESSED"
    -> "This Is All Caps and Should Be Addressed"
"EPISODE 7 — THE FORCE AWAKENS" -> "Episode 7 — The Force Awakens"
"episode 7 – The force awakens" -> "Episode 7 – The Force Awakens"
"THE CASE OF X ≤ 7" -> "The Case of X ≤ 7"
"the case of X ≤ 7" -> "The Case of X ≤ 7"
"'QUOTE' A GREAT" -> "'Quote' a Great"
"‘QUOTE’ A GREAT" -> "‘Quote’ a Great"
"“YOUNG AND RESTLESS”" -> "“Young and Restless”"
"YEA NO" -> "Yea No"
"ÝÆ ÑØ" -> "Ýæ Ñø"
"yea no" -> "Yea No"
"ýæ ñø" -> "Ýæ Ñø"
"EL NIÑO A ARRIVÉ HIER" -> "El Niño a Arrivé Hier"
"FOO BAR 5TH ST" -> "Foo Bar 5th St"
"foo bar 5th st" -> "Foo Bar 5th St"
"34th 3rd 2nd" -> "34th 3rd 2nd"
"2lmc Spool: 'gruber on OmniFocus and vapo(u)rware'"
    -> "2lmc Spool: 'Gruber on OmniFocus and Vapo(u)rware'"
```

`but` and `a` in those all-caps lines become lowercase small words. `≤` and `7` and the em dash stay as their own tokens. `2lmc` starts with a digit, is not all consonants, and does not match `CAPFIRST`, so it stays `2lmc`. `OmniFocus` is kept by `UC_ELSEWHERE`. `vapo(u)rware` is an ordinary word; only `v` is uppercased.

Consonant acronyms:

```text
"Words with all consonants like cnn are acronyms"
    -> "Words With All Consonants Like CNN Are Acronyms"
```

`cnn` is three consonants, so it becomes `CNN`. `st` / `ST` has length 2, so it becomes `St`, not `ST`. `with` is not a small word.

`UC_INITIALS` tests in the suite are direct pattern checks: `A.B` matches, `A.B.` matches, `ABCD` does not. Implement that pattern. Do not special-case only those three strings.

## Callback and abbreviation file

The callback runs before every other per-token rule, including on recursive pieces.

Locked callback behavior, from the tests and README:

```text
"a simple tcp and udp wrapper"
    -> "A Simple TCP and UDP Wrapper"
```

`tcp` is three consonants, so it becomes `TCP` with no callback. `udp` contains a vowel and becomes `Udp`.

A callback that returns the uppercased token for `TCP` and `UDP` only:

```text
"a simple tcp and udp wrapper" -> "A Simple TCP and UDP Wrapper"
"A SIMPLE TCP AND UDP WRAPPER" -> "A Simple TCP and UDP Wrapper"
```

A callback that returns `AT&T` when `upper(token) == "AT&T"`:

```text
"at&t" -> "AT&T"
```

A callback that returns `upper(token)` for every token:

```text
"crème brûlée" -> "CRÈME BRÛLÉE"
```

Wordlist file containing exactly:

```text
UDP
PPPoE
```

```text
"sending UDP packets over PPPoE works great"
    -> "Sending UDP Packets Over PPPoE Works Great"
"SENDING UDP PACKETS OVER PPPOE WORKS GREAT"
    without a wordlist -> "Sending Udp Packets Over Pppoe Works Great"
    with that wordlist  -> "Sending UDP Packets Over PPPoE Works Great"
```

Mixed-case `UDP` and `PPPoE` are already preserved without a wordlist (`UDP` by the consonant rule or `UC_ELSEWHERE`, `PPPoE` by `UC_ELSEWHERE`). The file matters for the all-caps line, where those preserve rules do not produce `PPPoE` or `Udp`-avoiding `UDP` spellings beyond plain uppercase. `UDP` on an all-caps line becomes `UDP` even without a file, because after lowercasing it is an all-consonant acronym. `PPPOE` becomes `Pppoe` without a file.

Returning `None` from Python is the empty-string case in Go. The word is then processed normally. A handled token is immutable for the first/last small-word fixup only.

## Worked check: one all-caps line

Input line `EPISODE 7 — THE FORCE AWAKENS` is all-caps because uppercase does not change it.

Tokens: `EPISODE`, `7`, `—`, `THE`, `FORCE`, `AWAKENS`, separators are single spaces.

- `EPISODE` fails initials, apostrophe, `Mc`, honorific, inline period, and (because the line is all-caps) the internal-capital preserve. It is not a small word. No slash or hyphen. Lowercase to `episode`. Not all consonants. `CAPFIRST` yields `Episode`.
- `7` and `—` fail every match and stay themselves.
- `THE` becomes `the` by the small-word rule.
- `FORCE` becomes `Force`, `AWAKENS` becomes `Awakens`.
- First token `Episode` is unchanged by `SMALL_FIRST`. Last token `Awakens` is unchanged by `SMALL_LAST`.
- Joined: `Episode 7 — the Force Awakens`.
- `SUBPHRASE` matches `— the` (em dash, space, small word `the`) and capitalizes `the`.
- Result: `Episode 7 — The Force Awakens`.

## Ambiguities — do not guess

These points are not settled by a test. Do not invent a cleanup. Where a rule above is already explicit, implement that rule and treat a Python run as a check, not as a chance to "fix" the expression.

1. Two engines. Stdlib `re` is the fallback if `regex` is not installed. It uses `[A-Z]` / `[a-zA-Z]` for internal capitals and initials, and `\w` for the capitalizer, apostrophe tail, and inline period. `regex` uses Unicode letter and uppercase-letter properties. Tested strings match on both engines. Untested strings do not: a non-ASCII internal capital such as `niÑO` is preserved by `regex` and capitalised by `re`; `a.1` is an inline period for `re` (`\w`) and not for `regex` (`\p{Letter}`). This task standardizes on the `regex` patterns. Confirm that choice if a later test harness imports `titlecase` without installing `regex`.

2. Case mappings whose length changes, and context-sensitive mappings. Python `str.upper` / `str.lower` / `str.capitalize` use full Unicode case mapping (`ß` → `SS`, and the first character of `capitalize` can become two characters). Go's usual `unicode.ToUpper` / `strings.ToUpper` mapping is one rune to one rune. No test uses `ß`, `İ`, ligatures, or Greek final sigma. Check those against CPython before requiring them. The tested accents are one-to-one.

3. `SUBPHRASE` has no trailing word boundary and is case-sensitive. After small words have been lowercased, a complete small word after `: ` / `- ` / `— ` is capitalized, and the tests cover that. Because `a` is the first alternative, the same expression also matches a lowercase prefix of a longer token. No test covers a prefix that is not itself the small word (`: example.com` is safe because it does not start with a small-word alternative; `: a.b` is not in the suite). Implement the expression as written. Check prefix cases against CPython before adding them as tests.

4. CRLF. With `preserve_blank_lines`, each CR and each LF is a separate split, so one `\r\n` pair becomes an empty segment between them. Without the flag, a run of CR and LF is one break. Output is always joined with `\n`. The tests use `\n` only.

5. Other whitespace. `\s` includes form feed, vertical tab, and Unicode spaces beyond the four characters in the tests (U+00A0, U+0009, U+200A, U+2006). U+2028 and U+2029 are whitespace, not line breaks, because line splitting is only CR and LF. That split is untested.

6. A leading space makes the first token empty. `SMALL_FIRST` then edits the empty token, not the following word. `" a thing"` is not in the suite. The token walk above is what the source does.

7. `//` blocks slash splitting only when rule 8 is reached. `http://foo.com` never reaches it, because rule 6 keeps the token. A token such as `foo//bar` with no internal period is untested. Rule 8's guard is still part of the source.

8. All-caps tokens that the preserve rules do not catch are lowercased and then capitalised. `AT&T` on an all-caps line is not an initials match and is not kept by the internal-capital rule (that rule is disabled when the line is all-caps). The suite only places `AT&T` on mixed-case lines, where it is preserved. Follow the order of rules rather than special-casing `AT&T`.

9. Honorifics `DR` and `MRS` keep their tail. The suite only shows forms whose tail is already lowercase (`dr` → `Dr`).

10. `mCfoo` does not match `MAC_MC`. Untested.

11. Single-character remainder after `Mc` (`McA`, remainder length 1) does not match `MAC_MC`, because the remainder must match `\w.+`. Untested.

12. Callback immutability does not stop `SUBPHRASE`, and it does not survive a recursive return. Untested interactions. The control flow above is what the source does.

13. Wordlist files: Python opens them with the platform text encoding and no error handler beyond "file missing." The tests use an ASCII temp file. Duplicate keys keep the last line. Non-ASCII files and permission errors are unspecified.

14. `set_small_word_list('a|an|the|with')` would expect `Playing the Game "Words with Friends"` for `playing the game "words with friends"`. That test is skipped. The default expectation, if you need it, is `Playing the Game "Words With Friends"`, because `with` is not a default small word. Do not port the helper's shorter subphrase class `[:.;?!]` as the default. The live class also contains `- – ‒ — ―`.

15. Bytes input, `callback` returning `bytes`, and the CLI's stdin/file wrapping are unimplemented surface in this task. Do not invent them.

## Done when

- `Titlecase(s, nil)` matches Python `titlecase(s)` for the default flags on the behaviors above.
- Non-default `SmallFirstLast`, `PreserveBlankLines`, `NormaliseSpaceCharacters`, callback, and wordlist callback match the corresponding Python arguments.
- Recursive slash, hyphen, and `Mc` calls use the flags stated above.
- The Python package files are unchanged.
- No test file, dataset, or reward script is part of this step.
