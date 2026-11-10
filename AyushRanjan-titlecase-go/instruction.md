# Titlecase in Go

## Repository

This repository is a Python titlecase library. Its `titlecase` function converts a line of text to title case, applying the library's rules for small words, abbreviations, punctuation, and related cases. Those rules are defined by the Python implementation in this repository.

## What to build

Implement an equivalent titlecase program in Go in `/workspace/repo`. The program must read one title per line from standard input and write the corresponding titlecased result to standard output, one result per line.

## Requirements

- Use only the Go standard library.
- The solution must not contain or use any `.py` files.
- `go build ./...` must pass.
- For the provided inputs, the Go output must match the original Python library's `titlecase` behavior byte for byte.

## Not graded

Execution speed, memory usage, and exact error messages are not required to match.

## Grading

The task is evaluated with hidden automatic tests. Partial credit is possible.
