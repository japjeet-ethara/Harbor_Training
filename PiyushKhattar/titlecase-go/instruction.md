# Titlecase in Go

## What the repository is

`/workspace/repo` is the [python-titlecase](https://github.com/ppannuto/python-titlecase) checkout at commit `42f43e2de55bf003b286c6f8e8d8b2d26676a167` (2024-04-05 22:03:59 -0700), under The MIT License (MIT). Its `titlecase()` function, in `titlecase/__init__.py`, converts text to title case. It walks the text one line at a time and one whitespace-separated word at a time, keeps the first matching rule for each word, and lowercases the small words `a`, `an`, `and`, `as`, `at`, `but`, `by`, `en`, `for`, `if`, `in`, `of`, `on`, `or`, `the`, `to`, `v`, `v.`, `via`, `vs`, and `vs.`, except where a later rule capitalizes them. A line is all capitals when `line.upper() == line`. The rules cover blank lines, original whitespace, an optional per-word callback, dotted initials, `d'` / `l'` / `o'` forms, an `Mc` prefix, `Mr` / `Mrs` / `Ms` / `Dr`, an internal period, an uppercase letter later in a word, `/` and `-` splitting, all-capital lines, all-consonant acronyms, capitalizing the first letter, and small words at the start of a line, the end of a line, and after subphrase punctuation. Read that function as the specification, including the `REGEX_AVAILABLE` patterns (Unicode letter classes). Ignore the `re` fallback that is used only when the third-party `regex` module is not installed.

## What to build

Replace this repository with a Go program whose module root is `/workspace/repo`. Put `package main` in that directory so `go build -o /tmp/titlecase .` from `/workspace/repo` produces the program. The program takes no arguments. It reads titles from standard input and writes the titlecased titles to standard output, one result per input line.

Split input only on `\n`. If a line ends with `\r\n`, drop that trailing `\r` with the newline; any other `\r` is part of the title. A final title with no trailing `\n` is still a title. For each title string `s`, write the exact bytes returned by `titlecase(s)` with its default arguments, then one `\n`. The defaults are `callback=None`, `small_first_last=True`, `preserve_blank_lines=False`, and `normalise_space_characters=False`. Do not read a word list and do not supply a callback. An empty title is valid: `titlecase("")` is `""`, so an empty input line produces an empty output line. Empty input produces no output bytes.

## Hard rules

- Import only the Go standard library. Do not add third-party modules.
- No file whose name ends in `.py` may remain anywhere under `/workspace/repo`.
- `go build ./...`, run from `/workspace/repo`, must succeed.

## Behaviour

For every input, the bytes this program writes must be identical to processing each title with the Python `titlecase()` specified above and writing each result followed by `\n`.

## Not checked

Speed, memory use, and the wording of error messages are not graded.

## How it is graded

Hidden automatic tests grade the program. A program that is correct for only some inputs receives a partial score.
