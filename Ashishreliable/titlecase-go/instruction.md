# Port python-titlecase to Go

## Repository

`/workspace/repo` contains python-titlecase from https://github.com/ppannuto/python-titlecase at commit `42f43e2de55bf003b286c6f8e8d8b2d26676a167` (2024-04-05), package version 2.4.1, under the MIT License (Copyright 2021 Patrick William Pannuto). It is a Python port of Stuart Colville's titlecase.py, which was a port of John Gruber's titlecase.pl. The behavior to preserve is `titlecase()` in `titlecase/__init__.py`.

## Goal

Build a Go program in `/workspace/repo`. The directory must be a Go module whose main package is the module root, so that `go build .` and `go run .` work there. The program reads one title per line from standard input and writes the titlecased result to standard output, one line per input line.

A line is the text before each `\n`. The `\n` is not part of the string passed to `titlecase()`. Pass that string to the original `titlecase()` with its default arguments: no callback, `small_first_last=True`, `preserve_blank_lines=False`, and `normalise_space_characters=False`. Write exactly the returned string, then one `\n`. Do this for every line, including empty lines.

## Hard rules

- Use only the Go standard library. Do not add third-party Go modules.
- When you finish, no `.py` file may remain anywhere under `/workspace/repo`.
- `go build ./...` in `/workspace/repo` must succeed.

## Behaviour

For every input, standard output must match the original Python `titlecase()` byte for byte, using the line contract in Goal.

## Not graded

Speed, memory use, and the wording of error messages are not graded.

## Grading

Grading is automatic and hidden. A partial score is possible. The graded checks are a successful `go build ./...`, no `.py` files left under `/workspace/repo`, and exact standard output.
