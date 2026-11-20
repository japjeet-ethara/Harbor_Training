# Port `python-titlecase` to Go

## The repository

`/workspace/repo` contains the open-source Python project
[python-titlecase](https://github.com/ppannuto/python-titlecase) (MIT licence, version 2.4.1).
Its `titlecase()` function in `titlecase/__init__.py` turns a sentence such as
`the lord of the rings` into a properly capitalised title (`The Lord of the Rings`),
following a long list of small rules (small words, acronyms, hyphenated and slashed words,
names such as `McDonald` and `O'Neil`, URLs, initials, and more).

Python 3 and the project's optional `regex` package are installed in the container so that you
can run the original and compare. The original is the specification.

## What to build

Replace the Python implementation with a Go program at the root of `/workspace/repo`:

- `/workspace/repo/go.mod` is the Go module, and the `main` package lives directly in
  `/workspace/repo` (so that `go build .` produces the program).
- The program reads UTF-8 text from standard input, one title per line (lines end with `\n`,
  and no line contains `\r`), and writes the titlecased result of each line to standard
  output, one per line, each followed by `\n`.
- The result for each input line must be exactly what the original
  `titlecase(line)` returns for that line, with default arguments and with the `regex`
  package available (the Unicode-aware code path of the original). The output must match
  byte for byte, for every possible input line, including lines with non-ASCII letters,
  unusual punctuation, tabs, other whitespace characters, and leading or trailing spaces.

## Hard rules

- Go standard library only. No third-party modules, no cgo.
- The program must be self-contained: it must not start other programs (no `os/exec`) and
  must not need Python at run time.
- When you finish, no `.py` files may remain anywhere under `/workspace/repo`.
- `go build ./...` must pass in `/workspace/repo` with the Go toolchain in the container
  (Go 1.23).

## Not checked

Speed, memory use, error message wording, code style, documentation, and unit tests.

## How it is graded

Hidden automatic checks run against what is in `/workspace/repo` after you finish, and the
score is partial:

1. The Go program builds.
2. No Python files remain and the rules above are respected, and the program builds.
3. The program's output on a large set of titles that you have not seen, measured as the
   share of lines that match the original's output exactly.
