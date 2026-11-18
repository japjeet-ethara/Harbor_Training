## Repository Overview

`/workspace/repo` contains the Python implementation of `titlecase()` from `python-titlecase`, a library that applies title capitalization rules for small words, punctuation, acronyms, compound words, and case-preserving forms.

## Task

Build a Go program in `/workspace/repo` that reads one title per line from `stdin` and prints the titlecased result to `stdout`, one per line.

## Hard Rules

- Use the Go standard library only; do not add external third-party modules.
- Delete all `.py` files anywhere under `/workspace/repo`, including subdirectories, before finishing.
- `go build ./...` in `/workspace/repo` must succeed with exit code 0.

## Behaviour

For every input line, the output must match the original Python `titlecase()` output byte-for-byte.

## Not Checked

Execution speed, memory usage, and error message wording.

## Grading

Graded automatically using hidden test inputs with partial scoring across build verification, Python file removal, and exact line-by-line output accuracy.
