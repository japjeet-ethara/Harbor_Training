# Port python-titlecase to Go

`/workspace/repo` contains the Python library `titlecase` (MIT licence). It converts a string to proper title case: small words stay lowercase, acronyms and special tokens are preserved, URLs are left alone, and so on.

## What to build

A Go module whose main package is the root of `/workspace/repo`. It reads one title per line from standard input and prints the titlecased result, one line per input line.

`go build -o titlecase .` run in `/workspace/repo` must produce that program.

## Hard rules

- Go standard library only. No third-party modules, and no import path outside the standard library.
- `go build ./...` must succeed in `/workspace/repo`.
- When you finish, no `.py` file may remain anywhere under `/workspace/repo`.

## Behaviour

For every input line, the matching output line must be the same bytes the original Python `titlecase()` function returns for that line, using its default arguments (no callback, small words capitalized at the ends, blank lines not preserved, spaces not normalised).

## Not checked

Speed, memory usage, and the wording of error messages.

## Grading

Hidden automatic tests give a partial score for three things: the build, no Python files left, and output correctness on a hidden set of inputs.
