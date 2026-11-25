# Title Case in Go

## 1. Task Overview

Build a Go program that converts text to Title Caps the way `python-titlecase` 2.4.1 does. The program is a command-line tool. It reads text from arguments, standard input, or a file, applies the title-casing rules below, and writes the result to standard output or a file.

The conversion is a best-effort, line-by-line process. It does not simply capitalise every word. Small words such as "a" and "the" usually stay lowercase in the middle of a line, while abbreviations, initials, domains, and some acronyms are left alone or restored by a fixed set of heuristics. The rules were written for American English. They are not context-aware: the program cannot tell the pronoun "us" from the abbreviation "US".

## 2. Original Repository Information

The behaviour to reproduce is the Python package in this repository:

- Repository: https://github.com/ppannuto/python-titlecase
- Commit: `42f43e2de55bf003b286c6f8e8d8b2d26676a167`
- Commit date: 2024-04-05 22:03:59 -07:00
- Package version in that commit: 2.4.1
- Licence: MIT. Copyright (c) 2021 Patrick William Pannuto

Lineage, as stated by the package:

1. John Gruber's Perl script `titlecase.pl` (10 May 2008).
2. Stuart Colville's Python port `titlecase.py`.
3. Patrick William Pannuto's maintained resurrection of that port.

The Python console script is declared as `titlecase = titlecase.__init__:cmd`. Match that command's options and the `titlecase()` transformation it calls. When the optional third-party `regex` package is installed, the Python module uses Unicode letter classes. Implement that Unicode-aware behaviour. The standard-library `re` fallback is a narrower path and is not the behaviour to reproduce.

## 3. Main Objective

Produce an executable at `/app/titlecase`.

Running that executable must give the same text result as the Python `titlecase` command from the commit above, for the same arguments, the same input text, and the same acronym wordlist. The Go program must perform the conversion itself. It must not call the Python package, the Python interpreter, or another title-casing program.

From `/app`, this build must succeed:

```bash
go build -o /app/titlecase .
```

## 4. Functional Requirements

The executable supports the following interface. Short options must not be treated as prefixes of longer options.

- Positional arguments are the words of the text to convert. They are joined with a single space, in order.
- `-f` / `--input-file PATH` reads the text from a file. The path `-` means standard input.
- `-o` / `--output-file PATH` writes the result to a file. The path `-` means standard output. An existing file is overwritten.
- `-w` / `--wordlist PATH` reads an acronym list from that file.
- `--preserve-blank-lines` keeps blank lines. Without this flag, blank lines are removed as described below.

Positional text and `--input-file` cannot be used together. If neither is given, read standard input.

If `--wordlist` is omitted, read `~/.titlecase.txt` from the current user's home directory when that file exists. A missing wordlist file is not an error. In that case, convert the text with no acronym overrides.

The wordlist file contains one acronym per line. Empty lines are ignored, and each remaining line is stripped of surrounding whitespace. Lookup is case-insensitive. The spelling on the matching line is the spelling written into the output. If the same acronym appears more than once, the later line wins. The override replaces the whole whitespace-separated token only when the token, compared case-insensitively, equals the acronym.

On success, exit with status 0. On a usage error, such as an unknown option or positional text combined with `--input-file`, exit with a non-zero status and do not write a converted title.

These Python functions are not part of the command and must not be added as options or modes:

- `set_small_word_list`
- a caller-supplied callback other than the wordlist file
- `normalise_space_characters`

The small-word list is fixed. Original whitespace characters are always kept.

## 5. Input and Output Format

Input and output are Unicode text.

The program writes only the converted text. It does not add a banner, a trailing newline of its own, or any other character beyond the conversion result. If the input has no final newline, the output does not gain one.

Processing order:

1. Split the input into lines.
2. Convert each line independently.
3. Join the converted lines with `\n` (U+000A), whatever newline form the input used.

Without `--preserve-blank-lines`, split on each run of one or more `\r` or `\n` characters. A run at the start or end of the input still produces an empty line in the joined output, so a single trailing newline is preserved. Consecutive blank lines disappear because the whole run is one separator.

With `--preserve-blank-lines`, split on every individual `\r` or `\n`. Each one becomes a line break, and empty lines stay in the output. A Windows `\r\n` pair therefore becomes two breaks.

Inside a line, split on each whitespace character and keep those separators. Convert the tokens, then put the original separators back between them. Tabs, non-breaking spaces, and repeated spaces stay as they were. A leading or trailing separator produces an empty token.

These published examples show the required results:

| Input | Output |
|---|---|
| `this is a test` | `This Is a Test` |
| `THIS IS A TEST` | `This Is a Test` |
| `this is a TEST` | `This Is a TEST` |
| `a thing` | `A Thing` |
| `make me a title` | `Make Me a Title` |
| `Can pipe and/or whatever else` | `Can Pipe and/or Whatever Else` |

`titlecase make me a title` prints `Make Me a Title`.

`echo "Can pipe and/or whatever else" | titlecase` prints `Can Pipe and/or Whatever Else`, followed by the newline that `echo` supplied.

With a wordlist entry `TCP`, `titlecase I LOVE TCP` prints `I Love TCP`.

A wordlist is what preserves an acronym the consonant rule does not recognise. Without a wordlist, `a simple tcp and udp wrapper` becomes `A Simple TCP and Udp Wrapper`. With `TCP` and `UDP` in the wordlist, it becomes `A Simple TCP and UDP Wrapper`.

## 6. Technical Requirements

- Implement the program in Go.
- The executable path is `/app/titlecase`.
- `go build -o /app/titlecase .` must work when run from `/app`.
- The target operating system is Linux.
- Use Unicode case conversion and Unicode letter categories equivalent to `\p{Letter}` and `\p{Uppercase_Letter}`.
- Read and write files as text. Do not add a byte-order mark.
- A wordlist override is applied to the original token before the other per-word rules. If it supplies a value, use that value exactly and skip the remaining per-word rules for that token. The first-and-last small-word adjustment also skips that token. The sub-phrase scan in rule 14 still runs on the finished line.
- Apply the first matching per-word rule and then move to the next token.
- Slash, hyphen, and `Mc` recursion receive the wordlist. They do not receive `--preserve-blank-lines`, and they always keep whatever spaces appear inside the piece. The pieces are single tokens, so they do not contain the line's newline characters. Slash and hyphen recursion do not capitalise a small word just because it is the first or last piece of the compound. `Mc` recursion does apply that first-and-last adjustment inside the remainder.

## 7. Behaviour and Edge Cases

A line is all-caps when its Unicode uppercase form is equal to the line itself. An empty line, and a line of only digits or punctuation, is all-caps. Each line has its own all-caps flag, so one word can be treated differently because of the other characters on its line.

For every token, apply the first matching rule.

1. **Wordlist override.** If the wordlist returns a spelling for the whole token, use it and stop for this token.

2. **Uppercase initials, all-caps lines only.** If the line is all-caps and the token is a repetition of `X.` or `X.Y` groups made of uppercase letters and periods, keep the token unchanged. This covers forms such as `A.B`, `A.B.`, `D.C.`, and `U.S.A.`. It does not match a solid word such as `ABCD`.

3. **Apostrophe names.** If the token matches `d`, `l`, or `o`, then `'` or `‘` (U+2018), then one or more letters, with an optional ending of exactly two characters each of which is `'` or `s`, rebuild it as follows. The match is case-insensitive. When the first letter is `d` or `l`, lowercase that letter, keep the apostrophe, and uppercase the next character. When the first letter is `o`, uppercase that letter, keep the apostrophe, and uppercase the next character. Leave every later character unchanged, including internal capitals. Thus `o'reilly` becomes `O'Reilly`, `l'grange` becomes `l'Grange`, and `l'GranGe` stays `l'GranGe`. The right curly apostrophe `’` (U+2019) does not match this rule, so `l’grange` is handled by the later rules and becomes `L’grange`.

4. **`Mc` names.** If the token begins with `Mc`, `mc`, or `MC` and at least two more characters follow, of which the first is a word character, rewrite the prefix as `Mc` and title-case the remainder recursively with the first-and-last small-word adjustment enabled. `mctavish` becomes `McTavish` and `MCFOO-BAR` becomes `McFoo-Bar`. A bare `mc` does not match. `Mac` is not this prefix.

5. **Honorifics.** If the whole token is `mr`, `mrs`, `ms`, or `dr`, in any case, uppercase only its first character and leave the rest of the token unchanged. `mr` becomes `Mr` and `MR` stays `MR`. A following period prevents a match. `Mss` does not match.

6. **Protected tokens.** Keep the token unchanged when it contains a letter, a period, and another letter, in that order. This protects `example.com`, `del.icio.us`, `D.C.`, and `http://foo.com`. On a line that is not all-caps, also keep the token unchanged when a letter is followed later by an uppercase letter. This protects `iTunes`, `OmniFocus`, `PPPoE`, `MacDonalds`, and an uppercase token of two or more letters such as `TEST`. Because an all-caps line skips the second half of this rule, `THIS IS A TEST` does not keep `TEST` and becomes `This Is a Test`, while `this is a TEST` stays `This Is a TEST`.

7. **Small words.** If the whole token is one of the small words below, ignoring case, replace it with the lowercase form. Attached punctuation prevents a match.

   The small words are `a`, `an`, `and`, `as`, `at`, `but`, `by`, `en`, `for`, `if`, `in`, `of`, `on`, `or`, `the`, `to`, `v`, `v.`, `via`, `vs`, and `vs.`.

   Words that are not on this list are capitalised normally. In particular, `is`, `be`, `it`, `nor`, `off`, `out`, `up`, `down`, and `per` are not small words. `THIS IS A TEST` therefore becomes `This Is a Test`.

8. **Slash compounds.** If the token contains `/` and does not contain `//`, split it on `/`, title-case each piece recursively without the first-and-last small-word adjustment, and join the pieces with `/`. `word/word` becomes `Word/Word`. A small word inside the compound stays lowercase, so `and/or` stays `and/or`. A token containing `//` is not split here.

9. **Hyphen compounds.** If the token contains an ASCII hyphen `-`, split it on `-`, title-case each piece recursively without the first-and-last small-word adjustment, and join the pieces with `-`. `end-to-end` becomes `End-to-End`. Only the ASCII hyphen causes this split. En dashes, em dashes, and the other dashes in the punctuation set do not.

10. **All-caps lowering.** If the line is all-caps and the token is still being processed, lowercase the token before the remaining rules.

11. **Consonant acronyms.** If the token is longer than two characters and every character is an ASCII consonant, replace it with the uppercase form. The consonants are the ASCII letters except `a`, `e`, `i`, `o`, `u`, and `y`. `cnn` becomes `CNN` and `tcp` becomes `TCP`. `udp` becomes `Udp` because `u` is a vowel. `st` becomes `St` because it is only two letters. This test uses ASCII consonants only.

12. **Default capitalisation.** Otherwise, uppercase the first letter of the token. Leading characters from the punctuation set below are skipped, and the rest of the token is unchanged. `'that's` becomes `'That's`. A token that begins with a digit is unchanged, so `34th`, `3rd`, `2nd`, and `2lmc` stay as they are. A token that begins with a character outside the punctuation set, such as `«`, is also unchanged when that character blocks the first letter.

After every token on the line has been processed, apply these two line-level fixes.

13. **First and last small words.** On the first token, optional leading punctuation followed by a small word is capitalised: the first character of the small word is uppercased and the rest of that small word is lowercased. On the last token, a small word followed by at most one punctuation character is capitalised the same way. `a thing` becomes `A Thing`, and a final `of` becomes `Of`. This applies only to the first and last whitespace-separated tokens. It is skipped for a token supplied by the wordlist. It is also skipped inside slash and hyphen recursion, except that after those recursive calls return, the whole compound can still be the first or last token of the outer line. That is why a standalone `a-b` becomes `A-B`, while an internal `and/or` stays lowercase. If the line starts with whitespace, the first token is empty, so a following small word is not treated as the first word: ` a thing` becomes ` a Thing`.

14. **Sub-phrase small words.** Scan the reassembled line. When one of `:`, `.`, `;`, `?`, `!`, `-`, `–` (U+2013), `‒` (U+2012), `—` (U+2014), or `―` (U+2015) is followed by exactly one ordinary space and then a small word, capitalise that small word. A comma does not trigger this. The pattern has no trailing word boundary. `Word: a trick` becomes `Word: A Trick`. Because a period counts, `Mr. and Mrs. Person` becomes `Mr. And Mrs. Person`.

The punctuation set used by the first-letter, first-small-word, last-small-word, and mixed-case rules is:

```text
!"“#$%&'‘()*+,-–‒—―./:;?@[\]_`{|}~
```

It includes the left double quote `“`, the left single quote `‘`, the en dash, the figure dash, the em dash, and the horizontal bar. The right quotes `”` and `’` are not in the set. An ampersand or similar mark inside a token stays in place. `Q&A` is capitalised by the normal first-letter rule. On a mixed-case line, `AT&T` is kept by the protected-token rule.

Domains and URLs follow the same rules. A token with an internal period is preserved, so `this is just an example.com` becomes `This Is Just an example.com` and `this is http://foo.com` becomes `This Is http://foo.com`. A token with `//` and no internal period is not preserved that way: `http://localhost` becomes `Http://localhost`.

Accented Latin text follows Unicode letter casing. `El Niño` stays `El Niño`, `EL NIÑO` becomes `El Niño`, and `ÝÆ ÑØ` becomes `Ýæ Ñø`. This is still a heuristic for American English, and other languages may not come out as a fluent speaker would expect.

## 8. Acceptance Criteria

The task is complete when all of the following are true:

- `/app/titlecase` exists and `go build -o /app/titlecase .` succeeds from `/app`.
- The program implements the conversion in Go.
- Positional arguments, standard input, `--input-file`, `--output-file`, `--wordlist`, and `--preserve-blank-lines` behave as specified above, including the path `-` and the default `~/.titlecase.txt` wordlist.
- Positional text combined with `--input-file` is rejected with a non-zero status.
- For the same text, flags, and wordlist, the output is byte-for-byte the same as the Python command from commit `42f43e2de55bf003b286c6f8e8d8b2d26676a167`, using that package's Unicode-aware rules.
- Small words, first and last words, sub-phrases, apostrophe names, `Mc` names, honorifics, initials, protected capitals, domains, slash and hyphen compounds, all-caps lines, and consonant acronyms follow section 7.
- Original spacing inside a line is preserved, blank lines follow the selected line-splitting mode, and lines are joined with `\n`.
- The program does not add options or modes for `set_small_word_list`, an arbitrary callback, or space normalisation.
