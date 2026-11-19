# Port `python-titlecase` to Go

## 1. Repository Overview

`/workspace/repo` contains a snapshot of `ppannuto/python-titlecase` (commit `42f43e2de55bf003b286c6f8e8d8b2d26676a167`, MIT License), a Python implementation of John Gruber's title-casing filter (`titlecase/__init__.py`). It converts input text to title case while preserving small words (such as `a`, `an`, `and`, `at`, `by`, `for`, `in`, `of`, `on`, `or`, `the`, `to`, `via`, `vs.`), acronyms, dotted initials, camelCase/internal uppercase words, URLs/inline-period domains, apostrophe prefixes (`d'`, `l'`, `O'`), `Mc`/`MC` prefixes, honorifics, hyphenated and slashed compounds, and subphrase capitalization after punctuation.

## 2. What to Build

Build a Go program in `/workspace/repo` (with a valid `go.mod` in `/workspace/repo` and a `main` package at the module root `/workspace/repo` so `go run .` or `go build -o <bin> .` builds the executable) that:
- Reads titles from standard input (`stdin`), one title per line (`\n`-delimited, stripping the trailing `\n` or `\r\n` before processing each line).
- Applies the exact `titlecase(line)` transformation from `titlecase/__init__.py` (with default options: `callback=None`, `small_first_last=True`, `preserve_blank_lines=False`, `normalise_space_characters=False`, and standard Python `re` behavior where `REGEX_AVAILABLE` is `False`) to each input line independently.
- Prints each resulting titlecased line to standard output (`stdout`) followed by `\n`, preserving a 1-to-1 correspondence with the input lines (including empty lines).

## 3. Hard Rules

- **Go standard library only**: `go.mod` must have zero external dependencies (`require` directives).
- **No Python files**: No `.py` files may remain anywhere inside `/workspace/repo` (including subdirectories).
- **Clean build**: `go build ./...` executed in `/workspace/repo` must succeed with exit code `0`.

## 4. Behaviour

For every input line, the printed output line must match the original Python `titlecase(line)` output byte for byte.

## 5. Not Checked

- Execution speed or memory usage.
- Error message wording on invalid CLI arguments.
- Code formatting or style.

## 6. How It Is Graded

Your submission is graded automatically after you finish by hidden verification checks with partial scoring across three weighted components:
- `build` (weight 1): `go build ./...` succeeds in `/workspace/repo`.
- `no_python` (weight 1): no `.py` files exist anywhere under `/workspace/repo` and `go build ./...` succeeds.
- `behaviour` (weight 4): the built Go binary is run against hidden test inputs on `stdin`, scored by the fraction of output lines that match the hidden reference outputs byte for byte.

