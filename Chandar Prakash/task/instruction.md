# Implement Titlecasing in Go

## Repository

This task is based on a Python implementation of titlecasing. It handles small words, acronyms, punctuation, apostrophes, prefixes, hyphenated and slash-separated words, whitespace, and special capitalization and line-handling cases.

## Task

Implement a Go program in `/workspace/repo` that reads titles from standard input, one title per line, and writes the titlecased result for each title to standard output, one result per line.

## Requirements

- Use only the Go standard library.
- Do not leave any Python files anywhere in the repository.
- `go build ./...` must pass.

## Expected behavior

For each input title, the program's output must match the original Python `titlecase()` implementation byte for byte. Answers come from titlecase **without the optional `regex` package**.

## Evaluation

The verifier checks 100,000 fixed-seed titles with frozen answers. Build and repository restrictions are prerequisites; reward is based only on the fraction of outputs that match exactly, with exactly one output line required per input line.

## Not evaluated

Speed, memory usage, and the wording of error messages are not evaluated.
