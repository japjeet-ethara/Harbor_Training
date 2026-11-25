# Port python-titlecase to Go

## Repository

`/workspace/repo` is a checkout of [python-titlecase](https://github.com/ppannuto/python-titlecase) (MIT licence, version 2.4.1). Its `titlecase()` function turns a title such as `the lord of the rings` into `The Lord of the Rings`. It applies many small rules (small words, acronyms, hyphens, slashes, apostrophes, `Mc` names, and so on) that are written with Python regular expressions, including look-ahead and look-behind tricks that Go's `regexp` package does not have.

## What to build

Replace the Python program with a Go program in `/workspace/repo`.

- `/workspace/repo/go.mod` must exist, and the `main` package must be in the repository root, so that `go build .` there produces the program.
- The program reads titles from standard input, one per line, and writes the titlecased result to standard output, one line per input line, each ending in `\n`.
- Every input line is independent. Input is UTF-8 and never contains `\r`. Titles use ASCII letters, digits, spaces, tabs and punctuation (including some non-ASCII punctuation such as curly quotes and dashes). A line may have leading, trailing or repeated whitespace.

## Hard rules

1. Go standard library only: no third-party modules, and the program must not start other programs or interpreters (no `os/exec`, no `plugin`).
2. When you finish, no `.py` file may exist anywhere under `/workspace/repo`. Only the Go version is left.
3. `go build ./...` must pass in `/workspace/repo`.

## Behaviour

For every input line, the output must match the original Python `titlecase(line)` byte for byte, called with default arguments on that single line. The reference is the code path used when the optional `regex` package is not installed (the standard `re` module). That is the situation in this container, so you can run the original with `python3` from `/workspace/repo` while you work, before you delete it.

## Not checked

Speed, memory use, and the wording of error messages.

## How it is graded

Hidden automatic tests give a partial score between 0 and 1 from three checks: the Go build, the rules above (no Python left, standard library only), and, with the largest weight, the share of hidden input lines for which your output is identical to the original's.
