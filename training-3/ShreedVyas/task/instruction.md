# Repository

python-titlecase is a Python implementation of titlecasing, as documented in [NOTES.md](NOTES.md).

# What to build

Create a Go module at the root of `/workspace/repo` with `go.mod` and a `package main` program that reads one title per input line from stdin and prints its titlecased result on one output line.

# Hard rules

Use only the Go standard library.

No `.py` file may remain anywhere in `/workspace/repo`.

`go build ./...` must pass.

# Behaviour

For every input, output must match the original Python `titlecase()` byte for byte.

The answer key uses standard-library `re`, with no optional `regex` package installed.

# Not checked

Speed, memory use, and error-message wording are not checked.

# How it is graded

Hidden automatic tests determine the score, with partial credit for passing checks.
