# Rewrite python-titlecase in Go

## What is in the repository

`/workspace/repo` holds version 2.4.1 of **python-titlecase**, a small MIT-licensed Python
library. Its only public function, `titlecase(text)` in `titlecase/__init__.py`, turns one
line of text into a headline: the first letter of most words is made upper case, short
words such as "a", "of" or "the" are kept lower case except at the start or end of the
line, and there are extra rules for things like acronyms, "Mc" surnames, words with an
apostrophe, hyphenated or slashed words, web addresses and lines typed entirely in capitals.

## Your job

Replace the Python library with a Go command line program that behaves the same way.

- `/workspace/repo` becomes the root of a Go module. Its root package is `package main`.
  `go build -o /tmp/titlecase .` run inside `/workspace/repo` must produce the program.
- The program reads UTF-8 text from standard input. Every input line is terminated by a
  single `\n`.
- For every input line, in the same order, it prints the titlecased line followed by `\n`
  on standard output. Exactly one output line per input line; nothing else is printed.
- The program ignores its command line arguments.
- When you are finished, there must be no file ending in `.py` anywhere under
  `/workspace/repo`, including inside `__pycache__` folders.

## Rules

- Standard library only. `go.mod` must not contain a `require` or a `replace` directive,
  and the code must not use cgo. The program is compiled with the Go 1.23 toolchain in this
  image, offline (`GOTOOLCHAIN=local`, `GOPROXY=off`, `GOFLAGS=-mod=mod`, `CGO_ENABLED=0`).
- `go build ./...` must succeed inside `/workspace/repo`.
- The program must compute the result on its own. It must not start another program, read
  any file, or open any network connection. The grader runs it as an unprivileged user in a
  container that has no Python and no network.

## Required behaviour

For every input line, the output line must be identical, byte for byte, to the value of
`titlecase(line)` from the original library, called with default arguments while the
optional `regex` package is importable (`titlecase.REGEX_AVAILABLE` is `True`). Both
`python3` and the `regex` package are installed in this image, so you can run the original
on any text you like.

The input lines are valid UTF-8 and never contain `\r`, `\n` or any other line separator.
They are mostly English made of ASCII letters, digits and punctuation. They can also contain
Latin letters with diacritics (for example `é`, `ñ`, `ø`, `æ`, `ß`), curly quotes and
dashes, other non-ASCII punctuation and symbols (for example `¿`, `¡`, `≤`, `€`), and
whitespace characters other than the plain space, such as the tab, the no-break space, the
thin space or the ideographic space. A line may begin or end with whitespace, and may
contain several whitespace characters in a row. Every whitespace character must be kept
exactly as it was.

## Not graded

Speed, memory, code style, error messages, and what happens on input that is not valid
UTF-8.

## Grading

Automatic, hidden tests produce a score between 0 and 1 made of three parts:

1. **build** (weight 1): `go build ./...` and the build of the root program succeed, with
   a standard-library-only `go.mod`.
2. **no_python** (weight 1): the build succeeds and no `.py` file remains in the
   repository.
3. **behaviour** (weight 4): the share of hidden input lines for which the program's output
   line is byte-identical to the original library's output.

The final score is the weighted mean of the three parts.
