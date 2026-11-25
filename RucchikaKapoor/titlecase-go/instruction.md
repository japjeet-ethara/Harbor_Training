# Port python-titlecase to Go

`/workspace/repo` contains **python-titlecase**, a Python library whose `titlecase()` function converts a
line of text into a properly capitalised title (for example `the lord of the rings` becomes
`The Lord of the Rings`). The logic lives in `titlecase/__init__.py` and relies on regular
expressions with look-ahead, look-behind and back-references.

## What to build

Replace the Python project with a Go program in `/workspace/repo` that reads one title per line from
standard input and prints the titlecased result, one per line, to standard output. The Go program
must be a `package main` at the root of `/workspace/repo`, with a `go.mod` file.

## Hard rules

- Use the Go standard library only (no third-party modules).
- No `.py` files may remain anywhere in `/workspace/repo` when you finish.
- `go build ./...` run in `/workspace/repo` must succeed.

## Behaviour

For every input line, the output line must match what the original Python `titlecase()` function
returns for that line, byte for byte. This includes rare cases and unusual spacing and punctuation.

## Not checked

Speed, memory use and the wording of error messages.

## How it is graded

The project must build and contain no Python files to be eligible for a score. The behavior score
is the fraction of hidden cases whose output records match the original implementation exactly.
The program must emit exactly one output record per input line; missing or extra records receive no
behavior credit. A behavior score below 20% receives no reward.
