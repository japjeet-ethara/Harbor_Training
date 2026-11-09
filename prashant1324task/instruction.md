# Task: Port Python Titlecase to Go

## Objective

Port the existing Python `titlecase` library in this repository to Go. The Go implementation must reproduce the original Python implementation's behaviour as closely as possible.

## Requirements

1. Implement the titlecase functionality in Go.
2. Read input from standard input, processing one title per line.
3. Write the corresponding titlecased result to standard output, with one output line for each input line.
4. Preserve the original implementation's behaviour, including its word-capitalization rules, punctuation handling, apostrophes, hyphenated words, slash-separated words, initials, and special cases.
5. Match the original Python implementation's output exactly, including capitalization and spacing.
6. Use only the Go standard library. Do not add external Go dependencies.
7. The project must compile successfully using:

   `go build ./...`

8. Do not use or depend on Python in the Go implementation.
9. Remove all `.py` files from the final implementation.
10. Keep the implementation organized, readable, and maintainable.

## Important constraints

- The original Python implementation is provided as a reference for understanding the required behaviour.
- Do not modify the original reference implementation to make the Go port pass.
- Do not hardcode outputs for individual inputs.
- The implementation must work for arbitrary input titles, not just a fixed set of examples.
- Do not add unnecessary external dependencies or runtime requirements.

## Completion criteria

The task is complete when the Go implementation builds successfully, uses no Python files, and reproduces the original Python library's titlecasing behaviour.
