# Python `titlecase` --- Source Notes

## 1. Project identity

-   Repository: `https://github.com/ppannuto/python-titlecase`
-   Source file: `titlecase/__init__.py`
-   Source version declared in code: `2.4.1`
-   Commit checked locally: `42f43e2de55bf003b286c6f8e8d8b2d26676a167`
-   Commit date: `2024-04-05T22:03:59-07:00`
-   Licence: MIT (`LICENSE.txt`)

## 2. Purpose

The `titlecase()` function converts text into title case. It capitalizes
words while generally leaving certain short joining words lowercase. It
also applies special rules for punctuation, names, acronyms, hyphenated
words, slash-separated words, whitespace, and line breaks.

The source file also provides: - A callback mechanism for custom word
handling. - A helper to load custom abbreviations from a file. - A
command-line interface (`cmd()`).

## 3. Small-word list

The default small-word expression is:

`a | an | and | as | at | but | by | en | for | if | in | of | on | or | the | to | v | v. | via | vs | vs.`

These words are generally lowercased when they occur as standalone
words. The matching is case-insensitive.

There are exceptions: - A small word at the beginning of a title is
capitalized by the `SMALL_FIRST` rule. - A small word at the end of a
title is capitalized by the `SMALL_LAST` rule. - A small word following
certain punctuation plus a space is capitalized by the `SUBPHRASE` rule.

The list can be replaced at runtime using
`set_small_word_list(small=...)`.

## 4. Main processing flow

The
`titlecase(text, callback=None, small_first_last=True, preserve_blank_lines=False, normalise_space_characters=False)`
function:

1.  Splits the input into lines. With `preserve_blank_lines=True`, it
    splits on each CR or LF character; otherwise, runs of CR/LF
    characters are treated as one separator.
2.  For each line, checks whether the entire line is uppercase
    (`line.upper() == line`).
3.  Splits the line on whitespace while retaining the whitespace pieces.
4.  Processes each word in order.
5.  Applies special rules and capitalization.
6.  Applies first-word and last-word small-word rules when enabled.
7.  Reconstructs the line, preserving original whitespace unless space
    normalization is enabled.
8.  Capitalizes small words that begin a subphrase after selected
    punctuation.
9.  Joins processed lines with `\n`.

## 5. Word-handling rules

### 5.1 Callback has first priority

If a callback is supplied, it is called for each word with `all_caps` as
a keyword argument. If it returns a truthy value, that returned text is
used and marked immutable so later first/last-word processing does not
alter it.

### 5.2 All-uppercase initials

If the original line is all uppercase and a word matches the
`UC_INITIALS` pattern, that word is preserved unchanged. Examples of the
pattern include sequences such as `U.S.` and `A.B.C.`.

### 5.3 Apostrophe-prefixed forms

The `APOS_SECOND` pattern recognizes words beginning with `d`, `o`, or
`l` followed by an apostrophe-like character. The code capitalizes the
letter after the apostrophe. For a single initial consonant, the first
letter is lowercased; otherwise, the first letter is uppercased.

This is a specialized rule; verify exact examples against the original
implementation.

### 5.4 Mc names

Words matching `MAC_MC` (beginning with `Mc` or `MC`) receive special
handling: the prefix is capitalized and the remainder is processed
recursively.

### 5.5 Titles

The `MR_MRS_MS_DR` pattern recognizes `m`, `mr`, `mrs`, `ms`, and `dr`
(case-insensitively). The first character is uppercased.

### 5.6 Existing internal capitalization and periods

A word is preserved unchanged if: - It contains a letter-period-letter
sequence (`INLINE_PERIOD`), or - The line is not all uppercase and it
matches `UC_ELSEWHERE`, which detects uppercase letters later in the
word after an initial portion.

This helps preserve forms such as dotted abbreviations and mixed-case
names/terms. The exact character coverage depends on whether the
third-party `regex` module is available.

### 5.7 Small words

A word matching `SMALL_WORDS` is converted to lowercase.
First/last/subphrase capitalization is handled in later processing.

### 5.8 Slash-separated words

If a word contains `/` but does not contain `//`, it is split on `/`.
Each part is recursively title-cased with `small_first_last=False`, then
the parts are joined using `/`.

### 5.9 Hyphenated words

If a word contains `-`, it is split on hyphens. Each part is recursively
title-cased with `small_first_last=False`, then the parts are joined
using `-`.

### 5.10 All-uppercase lines

For lines detected as all uppercase, words not handled by earlier
special cases are lowercased before normal capitalization. This means
the program does not simply preserve all uppercase words.

### 5.11 All-consonant words

A word consisting only of consonants is treated as an acronym if its
length is greater than two. Such a word is uppercased. The consonant set
excludes `a`, `e`, `i`, `o`, `u`, and `y`.

### 5.12 Normal capitalization

Other words are capitalized using the `CAPFIRST` regular expression. It
looks for the first eligible letter after leading punctuation and
uppercases the matched portion.

## 6. Punctuation and small-word boundaries

The `PUNCT` expression defines punctuation characters used by the
first-word and last-word patterns.

-   `SMALL_FIRST` can capitalize a small word at the beginning, allowing
    leading punctuation.
-   `SMALL_LAST` can capitalize a small word at the end, allowing
    trailing punctuation.
-   `SUBPHRASE` capitalizes a small word after selected punctuation
    followed by a space. The default pattern includes colon, period,
    semicolon, question mark, exclamation mark, and several dash
    characters.

The source defines `PUNCT` and the patterns near the top of the file.

## 7. Whitespace and line breaks

-   Words and whitespace are split separately so original whitespace can
    be reassembled.
-   By default, the program preserves the original whitespace characters
    within each line.
-   If `normalise_space_characters=True`, it joins processed words using
    ordinary single spaces.
-   `preserve_blank_lines=True` changes how CR/LF characters are split,
    allowing blank lines to be represented in the processed output.
-   The final processed lines are joined with `\n`.

These options affect output formatting and should be considered when
defining the Go task's required input/output interface.

## 8. Regex dependency and fallback

The module first tries to import the third-party `regex` package.

-   If available, `REGEX_AVAILABLE=True` and several patterns use
    Unicode properties such as `\p{Letter}` and `\p{Uppercase_Letter}`.
-   If importing it fails, the code falls back to Python's built-in `re`
    module and uses more limited character classes such as `\w` and
    `[A-Z]`.

Therefore, behaviour for non-ASCII letters can differ depending on which
regex implementation is installed. Record which dependency/environment
is used when generating reference outputs.

## 9. Custom abbreviation wordlist

`create_wordlist_filter_from_file(file_path)`: - Returns a no-op
callback if no path is supplied or the file does not exist. - Reads
non-empty lines from the file and strips surrounding whitespace. -
Builds a lookup using uppercase keys while preserving each
abbreviation's original spelling as the value. - Returns a callback that
looks up each word case-insensitively.

The CLI uses an explicit `--wordlist` path if supplied; otherwise it
defaults to `~/.titlecase.txt`.

## 10. Command-line interface

The `cmd()` function uses `argparse` and supports:

  -----------------------------------------------------------------------
  Option                              Meaning
  ----------------------------------- -----------------------------------
  Positional string arguments         Text to title-case; multiple
                                      arguments are joined with spaces.

  `-f`, `--input-file`                Read input from a file; `-` means
                                      standard input.

  `-o`, `--output-file`               Write output to a file; `-` means
                                      standard output.

  `-w`, `--wordlist`                  Use a custom abbreviation wordlist.

  `--preserve-blank-lines`            Preserve blank lines in input.
  -----------------------------------------------------------------------

If no positional text is supplied, input is read from the selected input
stream (standard input by default). Output goes to the selected output
stream (standard output by default).

## 11. Important functions and constants to inspect

  --------------------------------------------------------------------------
  Name                                   Role
  -------------------------------------- -----------------------------------
  `SMALL`                                Default small-word expression.

  `PUNCT`                                Punctuation characters used by
                                         boundary rules.

  `SMALL_WORDS`                          Matches standalone small words.

  `SMALL_FIRST`                          Handles small words at the
                                         beginning.

  `SMALL_LAST`                           Handles small words at the end.

  `SUBPHRASE`                            Handles small words after selected
                                         punctuation.

  `set_small_word_list()`                Replaces the small-word patterns.

  `titlecase()`                          Main title-casing implementation.

  `create_wordlist_filter_from_file()`   Loads custom abbreviation
                                         spellings.

  `cmd()`                                Command-line interface.
  --------------------------------------------------------------------------

## 12. Candidate examples to verify against the original program

These are useful cases to run through the original Python implementation
before treating them as confirmed expected outputs. Some depend on line
context, punctuation, or the regex dependency.

  -----------------------------------------------------------------------
  Input                               Expected behaviour to check
  ----------------------------------- -----------------------------------
  `the lord of the rings`             First/last small-word handling and
                                      lowercase middle small words.

  `a tale of two cities`              Small words in the middle.

  `war and peace`                     Small word in the middle.

  `dr smith`                          Special handling for `Dr`.

  `mcdonald`                          `Mc` name handling.

  `mother-in-law`                     Recursive hyphenated-word handling.

  `input/output`                      Recursive slash-separated handling.

  `NASA launches rocket`              Mixed case / uppercase-line
                                      behaviour.

  `U.S. history`                      Dotted-initial handling.

  `hello: the beginning`              Small word after subphrase
                                      punctuation.

  `hello   world`                     Preservation of repeated whitespace
                                      by default.

  `hello\n\nworld`                    Blank-line handling with both
                                      settings.
  -----------------------------------------------------------------------

**Important:** Run these examples using the checked-out Python version
and record the actual output. Do not assume this candidate table is a
complete or fully verified test oracle.

## 13. Scope note for the Go/Harbor task

The Harbor task instructions define the required Go program interface.
The Python source also has library features and CLI options that may be
outside that interface.

Before implementation: 1. Confirm the exact required input/output format
from `instruction.md`. 2. Confirm the Python dependency environment used
as the reference. 3. Generate expected outputs by executing the original
Python implementation. 4. Include edge cases for punctuation,
whitespace, line breaks, acronyms, hyphens, slashes, and Unicode where
supported. 5. Compare Go output byte-for-byte against the generated
reference output.

Do not remove or modify the original Python source while using it as the
reference implementation.
