# Port python-titlecase to Go

## Repository

`/workspace/repo` contains python-titlecase from https://github.com/ppannuto/python-titlecase at commit `42f43e2de55bf003b286c6f8e8d8b2d26676a167` (2024-04-05), package version 2.4.1, under the MIT License (Copyright 2021 Patrick William Pannuto). It is a Python port of Stuart Colville's titlecase.py, which was a port of John Gruber's titlecase.pl. The behavior to preserve is `titlecase()` in `titlecase/__init__.py`.

## Which original

`titlecase()` behaves differently depending on whether the optional `regex` package is installed, because `titlecase/__init__.py` picks a different set of patterns for `INLINE_PERIOD`, `UC_ELSEWHERE`, `CAPFIRST`, `APOS_SECOND` and `UC_INITIALS` at import time.

**The expected answers for this task come from titlecase WITHOUT the `regex` package**, that is the `import re as regex` branch, where `REGEX_AVAILABLE` is `False`. Match that branch.

This is not a detail. On the graded inputs the two modes give 6,583 different answers out of 100,000, so a port that matches the `regex` branch fails about 6.6% of the exam. The clearest difference is `[\w]` versus `[\p{Letter}]` in `CAPFIRST`: without `regex`, `_dream` stays `_dream`, because `_` is a word character and so absorbs the capitalisation; with `regex` it becomes `_Dream`.

The image contains no Python interpreter, so you cannot run the original. Read it.

## Goal

Build a Go program in `/workspace/repo`. The directory must be a Go module whose main package is the module root, so that `go build .` and `go run .` work there. The program reads one title per line from standard input and writes the titlecased result to standard output, one line per input line.

A line is the text before each `\n`. The `\n` is not part of the string passed to `titlecase()`. Pass that string to the original `titlecase()` with its default arguments: no callback, `small_first_last=True`, `preserve_blank_lines=False`, and `normalise_space_characters=False`. Write exactly the returned string, then one `\n`. Do this for every line, including empty lines.

## Hard rules

- Use only the Go standard library. Do not add third-party Go modules.
- When you finish, no `.py` file may remain anywhere under `/workspace/repo`.
- `go build ./...` in `/workspace/repo` must succeed.

## Behaviour

For every input, standard output must match the original Python `titlecase()` byte for byte, using the line contract in Goal and the mode in "Which original".

The graded inputs are not a sample of ordinary English titles. They include tabs, non-breaking and thin spaces, leading and trailing whitespace, the empty line, URLs, e-mail addresses, `//`, `_`-prefixed words, ordinals, all-caps hyphenated acronyms, decomposed (NFD) accents, and characters whose upper or title case is longer than one character, such as `ß`, `ﬁ`, `ŉ` and `İ`. Note that Go's `unicode.ToUpper` and `strings.ToUpper` are simple one-to-one mappings and cannot produce `SS`, `FI` or `ʼN`; Python's `str.upper()` can.

## Not graded

Speed, memory use, and the wording of error messages are not graded. The program is given 100,000 lines in a single run, so do not be quadratic.

## Grading

Grading is automatic and hidden. The graded checks run in a separate container that the agent never sees.

- A `.py` file left under `/workspace/repo` scores 0.
- A failing `go build ./...` scores 0.
- Otherwise the score comes only from output correctness on 100,000 hidden titles. Passing the first two checks is worth nothing on its own.
- A partial score is possible, but only near the top: below a 90% line match rate the score is 0, and byte-exact output on the whole stream is required for 1.0.