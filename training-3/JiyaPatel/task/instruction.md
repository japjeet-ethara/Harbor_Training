# Titlecase Go Port

## Repository
`/workspace/repo` contains `python-titlecase` (https://github.com/ppannuto/python-titlecase), a Python library implementing John Gruber's title-casing rules.

## Task
Build a Go program in `/workspace/repo` (with a valid `go.mod`) that reads one title per line from `stdin` and prints the titlecased result to `stdout`, one line per input line.

## Hard Rules
- Use the Go standard library only (no external third-party Go modules).
- Remove all `.py` files anywhere under `/workspace/repo` when finished.
- `go build ./...` in `/workspace/repo` must pass with exit code 0.
- The compiled binary or `go run .` in `/workspace/repo` must accept lines on `stdin` and output titlecased lines on `stdout`.

## Behaviour
- Output must match the original Python `titlecase()` function byte-for-byte for every input line, preserving whitespace, punctuation, small-word rules, inline uppercase/acronyms, URLs/emails, hyphenated and slash-separated compounds, apostrophes/contractions, and `Mac`/`Mc` prefixes.

## Not Checked
- Execution speed, memory usage, or stderr error message wording.

## Grading
- Graded automatically by hidden tests using weighted checks across build success, absence of `.py` files, and exact line-by-line output accuracy on a hidden test suite.
