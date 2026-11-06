## Repository

The workspace at `/workspace/repo` is a checkout of the Python project [python-titlecase](https://github.com/ppannuto/python-titlecase) at commit `42f43e2de55bf003b286c6f8e8d8b2d26676a167` (2024-04-05), version 2.4.1, released under the MIT License (Copyright (c) 2021 Patrick William Pannuto). Its public function, `titlecase()` in `titlecase/__init__.py`, splits text into lines and then into words and the whitespace between them, then applies an ordered set of rules: optional blank-line preservation, an optional per-word callback, all-caps initials, apostrophe-second names, Mc/Mac prefixes, the titles Mr/Mrs/Ms/Dr, inline periods, embedded capitals, the New York Times small-word list (plus `v` and `vs`), slash-separated and hyphenated parts, lowercasing of all-caps lines, consonant-only acronyms, default capitalization, capitalization of small words at the start and end of a line and after sub-sentence punctuation (`:`, `;`, `.`, `?`, `!`, or a dash followed by a space), and reassembly that keeps the original whitespace unless space normalisation is requested.

## What to build

Replace that Python project with a Go program in `/workspace/repo`. The program reads one title per line from standard input and writes the titlecased form of that line to standard output, one result per line. Use `titlecase()`’s default arguments: no callback, `small_first_last=True`, `preserve_blank_lines=False`, and `normalise_space_characters=False`.

## Hard rules

- Use only the Go standard library.
- No `.py` files may remain anywhere in the repository.
- `go build ./...` must pass.

## Behaviour

For every input line, the titlecased text written for that line must match the string returned by the original Python `titlecase()` implementation byte for byte.

## Not checked

Speed, memory usage, and error-message wording are not graded.

## Grading

The solution is evaluated using hidden automatic tests, with partial credit.
