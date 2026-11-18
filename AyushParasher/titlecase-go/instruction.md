# Titlecase migration

Migrate the vendored Python titlecase library to a Go stdin filter. For each input line, the result must equal `titlecase(line)` from `titlecase/__init__.py` (python-titlecase 2.4.1) called with its default arguments. Read that file before removing it. Section 2 defines how lines are read and written. Section 4 defines the transformation, in the same order as that function.

## 1. Repository Overview

`/workspace/repo` starts as a copy of [python-titlecase](https://github.com/ppannuto/python-titlecase) 2.4.1 (MIT). Stuart Colville wrote it; Pat Pannuto maintains it. It is a Python port of Stuart Colville's `titlecase.py`, which is itself a port of John Gruber's `titlecase.pl`.

The library rewrites text into title case. It keeps a fixed list of small words in lowercase, drawn from the New York Times Manual of Style, plus `v`, `v.`, `vs`, and `vs.`. It also tries to leave abbreviations, initials, hostnames, and intentional internal capitals alone. The rules are American-English heuristics: they do not know that "us" and "US" are different words, and they only partly handle non-English text.

The behavior to port is the function `titlecase(text)` in `titlecase/__init__.py`. Its defaults are `callback=None`, `small_first_last=True`, `preserve_blank_lines=False`, and `normalise_space_characters=False`. The optional third-party `regex` package is not part of this task. Use the standard-library `re` patterns, the ones assigned when `import regex` fails. Those patterns run on Python 3 `str` values, so `\w`, `\s`, and `\b` are Unicode, while `[A-Z]` and `[a-zA-Z]` are ASCII.

The Python command-line tool, `~/.titlecase.txt`, custom abbreviation files, the callback argument, and `set_small_word_list()` are not part of the Go program.

## 2. Objective

Build a Go program in `/workspace/repo` that reads titles from standard input and writes titlecased titles to standard output.

- The repository root is the Go module, and the program is `package main` in that root, so `go build -o titlecase .` produces the filter.
- The program takes no arguments, reads no files, and writes only the titlecased lines to stdout.
- Decode stdin as UTF-8.
- Split input into lines on `\n`. If a line ends in `\r` because the input used `\r\n`, drop that `\r` before title-casing. Any other character, including a `\r` that is not the carriage return of a `\r\n` pair, stays inside the line.
- Title-case each line on its own by the rules in section 4. This includes empty lines. Do not pass the whole stdin buffer through one `titlecase()` call: that call deletes blank lines. One input line produces one output line.
- Write each result followed by `\n`, including the last line, and including an empty result. Empty stdin produces empty stdout. A stdin of `a\nb` with no final newline produces two output lines, `A\nB\n`.

Calling `titlecase(line)` once per line, with the defaults above, and then appending `\n`, is the required I/O behavior.

## 3. Hard Requirements

- Write the program in Go.
- Use only the Go standard library. `go.mod` must not require any module outside the standard library. `golang.org/x/text` is not allowed. Go's `unicode` and `regexp` packages are allowed.
- Delete every file under `/workspace/repo` whose name ends in `.py`, including files in subdirectories. Do this after you have taken the behavior you need from them.
- From `/workspace/repo`, `go build ./...` must succeed.
- The finished program must do the title-casing itself. It must not shell out to Python or to another titlecase implementation.

Go's `regexp` engine treats `\w`, `\s`, and `\b` as ASCII. Python 3's `re` treats them as Unicode. Implement the Python classes. A literal copy of those escapes into `regexp` will not match.

Case conversion must follow Python 3 `str.upper`, `str.lower`, and `str.capitalize` on the same Unicode text. `str.capitalize` uppercases the first character and lowercases the rest. Uppercasing one character can grow the string (`ß` uppercases to `SS`). Implement that with the standard library. Do not use `strings.Title`.

## 4. Expected Behaviour

For every input line, the bytes of the titlecased line must equal `titlecase(line)` under the rules below. Capitalization, punctuation, whitespace, and edge cases all count. Preserve characters you are not explicitly changing.

The three examples from the library README are:

| Input | Output |
| --- | --- |
| `this is a test` | `This Is a Test` |
| `THIS IS A TEST` | `This Is a Test` |
| `this is a TEST` | `This Is a TEST` |

Those rows are illustrations. The algorithm below is the contract.

### Patterns

Small words, case-insensitive, as a full word:

`a|an|and|as|at|but|by|en|for|if|in|of|on|or|the|to|v\.?|via|vs\.?`

Punctuation, written here as the characters inside the Python character class:

`!"“#$%&'‘()*+,-–‒—―./:;?@[\]_`{|}~`

That set includes ASCII quotes and apostrophes, the left double quote `“` (U+201C), the left single quote `‘` (U+2018), hyphen-minus, en dash `–`, figure dash `‒`, em dash `—`, and horizontal bar `―`. The right single quote `’` (U+2019) is not in this set.

Compile these as the Python source does:

- `SMALL_WORDS`: `^(small)$` with `IGNORECASE`.
- `SMALL_FIRST`: `^([punct]*)(small)\b` with `IGNORECASE`.
- `SMALL_LAST`: `\b(small)[punct]?$` with `IGNORECASE`.
- `SUBPHRASE`: `([:.;?!\-–‒—―][ ])(small)` with no ignore-case flag. The character after the punctuation is an ASCII space, U+0020, not a general whitespace class. Because the small-word alternation is not ignore-case here, only an already-lowercase small word matches, and the first alternative that matches at that position wins (`a` matches before `an`, and so on).
- `MAC_MC`: `^([Mm]c|MC)(\w.+)` with no ignore-case flag. The prefix is only `Mc`, `mc`, or `MC`. The remainder is at least two characters: one Unicode word character and then one or more of any character.
- `MR_MRS_MS_DR`: `^((m((rs?)|s))|Dr)$` with `IGNORECASE`. This is `mr`, `mrs`, `ms`, and `dr` in any casing. It does not match `mss`, `miss`, or a trailing period.
- `INLINE_PERIOD`: `[\w][.][\w]` with `IGNORECASE`, searched anywhere in the word.
- `UC_ELSEWHERE`: `[punct]*?[a-zA-Z]+[A-Z]+?`, matched at the start of the word. ASCII letters only. It does not need to consume the whole word.
- `CAPFIRST`: `^[punct]*?([\w])`, matched at the start. The replacement uppercases the whole match, which is the leading punctuation plus the first Unicode word character.
- `APOS_SECOND`: `^[dol]['‘][\w]+(?:['s]{2})?$` with `IGNORECASE`. The first character is `d`, `o`, or `l`. The second is `'` or `‘`. Then one or more Unicode word characters. Then, optionally, exactly two characters that are each `'` or `s`.
- `UC_INITIALS`: `^(?:[A-Z]\.|[A-Z]\.[A-Z])+$`. ASCII capitals only. The whole word must be a repetition of `A.` or `A.B` forms, so `D.C.` and `A.B.C` match.

`\w` means a Python 3 Unicode word character. `\b` is a boundary between a Unicode word character and a non-word character. `\s` is a single Python 3 Unicode whitespace character.

All-consonant detection uses this ASCII set and nothing else, case-insensitively:

`bcdfghjklmnpqrstvwxz`

`a`, `e`, `i`, `o`, `u`, and `y` are vowels for this test. A word qualifies only when every character is in that consonant set and the length is greater than 2.

### Per line

Let the line be the input line after removing its terminator.

1. The line is all-caps when `upper(line) == line`. Apply this to the whole line, before splitting. Digits and punctuation do not by themselves make a line mixed case. A character that grows or changes when uppercased, such as `ß`, makes the line mixed case.

2. Split the line on each Unicode whitespace character and keep the separators. Do this one character at a time, not on runs of whitespace. Two spaces therefore produce an empty word between them. Leading whitespace produces an empty first word. Trailing whitespace produces an empty last word. Those empty strings are real slots in the word list.

3. Process each word, including empty ones, in order. Stop at the first rule that accepts the word.

   1. If the line is all-caps and the word matches `UC_INITIALS`, keep it unchanged.
   2. If the word matches `APOS_SECOND`, rebuild it and keep that result. When the first character is not a vowel (`a`, `e`, `i`, `o`, `u`, in either case), lowercase that first character. Otherwise uppercase it. Leave the second character as it is. Uppercase the third character. Leave every character after the third as it is. This rule runs before all-caps lowercasing, so the tail is not lowercased.
   3. If the word matches `MAC_MC`, take `capitalize(prefix) + titlecase(remainder)`. `capitalize` is Python's: first character upper, the rest of the prefix lower, so `mc`, `Mc`, and `MC` all become `Mc`. Run the full algorithm on the remainder, including its own subphrase pass, with first-and-last small-word capitalization enabled.
   4. If the word matches `MR_MRS_MS_DR`, uppercase its first character and leave the rest of the characters as they already are. `mr` becomes `Mr`. `MRS` stays `MRS`.
   5. If `INLINE_PERIOD` matches anywhere in the word, keep the word unchanged. This applies on all-caps lines too, so a hostname stays in the case it arrived in.
   6. If the line is not all-caps and `UC_ELSEWHERE` matches at the start, keep the word unchanged. This preserves internal ASCII capitals such as `iTunes` and `AT&T`.
   7. If `SMALL_WORDS` matches the entire word, append `lower(word)`.
   8. If the word contains `/` and does not contain `//`, split on every `/`, keep empty segments, title-case each segment with first-and-last small-word capitalization turned off, and join the results with `/`.
   9. If the word contains ASCII `-`, split on every `-`, keep empty segments, title-case each segment with first-and-last capitalization turned off, and join with `-`. Only U+002D splits. En dashes, em dashes, figure dashes, and horizontal bars do not.
   10. If the line is all-caps, replace the word with `lower(word)` before the next two steps.
   11. If the word is all ASCII consonants and longer than two characters, append `upper(word)`.
   12. Otherwise apply `CAPFIRST`: uppercase the first Unicode word character, leaving any leading punctuation and the rest of the word unchanged.

4. If first-and-last capitalization is on and the word list is non-empty, update the slots after the per-word pass:

   - Rewrite slot 0 with `SMALL_FIRST`. The replacement is the leading punctuation plus `capitalize(small word)`.
   - Rewrite the last slot with `SMALL_LAST`. The replacement is `capitalize` of the whole match, which is the small word plus at most one trailing punctuation character.

   The first slot and the last slot are the first and last split fields, not the first and last non-empty fields. When they are the same single field, apply `SMALL_FIRST` first and `SMALL_LAST` second. A line of only `the` becomes `The`. A small word that is not in slot 0 stays lowercase even if leading whitespace sits in front of it. A small word that is not in the last slot is capitalized by `SMALL_LAST` only when it really is the last field.

5. Join the words back together with the original whitespace separators, in their original positions. Do not collapse, insert, or retarget spaces. Tabs, non-breaking spaces, and other Unicode spaces stay as they were. This is `normalise_space_characters=False`.

6. Run `SUBPHRASE` on the joined line. For each match, keep the punctuation and the single ASCII space, and replace the matched small word with `capitalize` of that match. This is what capitalizes a small word after `:`, `.`, `;`, `?`, `!`, or a dash when that dash is one of the dash characters in the `SUBPHRASE` class. A tab or a non-breaking space after the punctuation does not trigger it.

Slash splitting happens before hyphen splitting. A word that contains `//` is not slash-split; it can still be hyphen-split later unless an earlier rule kept it. Recursive calls use this same algorithm, including their own `SUBPHRASE` pass, with the first-and-last flag the caller passed.

## 5. Not Evaluated

These do not affect the result:

- Execution speed
- Memory consumption
- The exact wording of error messages

## 6. Grading

Hidden automatic tests grade the submission with partial scoring. The three scored outcomes are independent, and a submission can receive credit for each one it satisfies:

- Build success: `go build ./...` succeeds in `/workspace/repo`.
- Removal of Python files: no file under `/workspace/repo` still has a name ending in `.py`.
- Behavioural correctness: the program's stdout matches section 4 for the inputs under test.

A failure in one outcome does not erase credit for the others.
