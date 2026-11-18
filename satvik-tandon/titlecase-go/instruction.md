## Repository

This workspace contains the MIT-licensed `python-titlecase` project at commit
`42f43e2de55bf003b286c6f8e8d8b2d26676a167`. Its `titlecase()` function
implements title casing with rules for small words, acronyms, punctuation,
hyphens, slashes, apostrophes, names beginning with Mc/Mac, and existing mixed
capitalisation.

## Build

Replace the Python implementation with a Go program in `/workspace/repo`. The
program must read one title per line from standard input and print one
title-cased result per line to standard output.

## Requirements

- Use only the Go standard library.
- Remove every `.py` file from `/workspace/repo`.
- `go build ./...` must succeed in `/workspace/repo`.
- For every input title, the output must match the original Python
  `titlecase()` output byte for byte.

## Grading

Hidden automated tests award partial credit. Speed, memory consumption, and
error-message wording are not graded.
