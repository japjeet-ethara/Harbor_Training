# What the repository is

This repository contains the `python-titlecase` project, an MIT-licensed title-casing library whose `titlecase()` function converts text to title case while applying rules for small words, acronyms, mixed-case terms, and other special word forms. The upstream repository is https://github.com/ppannuto/python-titlecase, at commit `42f43e2de55bf003b286c6f8e8d8b2d26676a167`.

# What to build

Build a Go program in `/workspace/repo` that reads one title per line from standard input and prints the titlecased result, one per line.

# Hard rules

- Use only the Go standard library.
- Leave no `.py` files anywhere in the repository.
- `go build ./...` must pass.

# Behaviour

For every input, the output must match the original Python `titlecase()` byte for byte.

# Not checked

Speed, memory usage, and error message wording are not checked.

# How it is graded

The work is graded by hidden automatic tests, and partial credit is available.