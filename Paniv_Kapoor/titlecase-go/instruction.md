# Titlecase in Go

## Repository

python-titlecase (https://github.com/ppannuto/python-titlecase, commit `42f43e2de55bf003b286c6f8e8d8b2d26676a167`, MIT license) is a Python library that converts text to title case. Its `titlecase()` function capitalizes principal words and lowercases a fixed set of small words, except at the start or end of a line or immediately after a subphrase delimiter. It also applies special rules for hyphenated and slash-separated words, apostrophes, names beginning with "Mc", all-caps lines, consonant-only acronyms, and tokens that already contain internal capitals or periods. `/workspace/repo/NOTES.md` specifies that default behavior of `titlecase()` in `titlecase/__init__.py` at that commit, including the behavior that depends on the third-party `regex` package.

## What to build

Create a Go program in `/workspace/repo` whose `main` package is at the repository root. `go run .` must read one title per line from stdin and write the title-cased result, one per line, to stdout.

Treat both `\n` and `\r\n` as line endings. A final input line with no line ending still counts as one line. Remove the line ending, then title-case the remaining string exactly as `titlecase(text)` does with its default arguments: `callback=None`, `small_first_last=True`, `preserve_blank_lines=False`, and `normalise_space_characters=False`. Do not read an abbreviation word list. Write that result followed by `\n`, including after the last line.

The Go result for every line must match the original Python `titlecase()` output byte-for-byte. Implement the default rules in `/workspace/repo/NOTES.md`. Process each line on its own. The `preserve_blank_lines=True` and `normalise_space_characters=True` cases in that file are optional Python parameters; leave both disabled. Do not drop empty lines, and do not replace tabs or other spaces with a normal space.

## Hard requirements

- Use only the Go standard library.
- No `.py` files may remain anywhere in `/workspace/repo`.
- `go build ./...` must succeed.

## Not evaluated

Speed, memory usage, and error-message wording are not evaluated.

## Grading

The task is evaluated using hidden automatic tests. Partial credit is possible.
