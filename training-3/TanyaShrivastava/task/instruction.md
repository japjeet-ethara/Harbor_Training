# Port python-titlecase to Go

## The repository

`/workspace/repo` contains **python-titlecase** (version 2.4.1, MIT licence), a Python
library whose `titlecase()` function turns a string such as `the lord of the rings`
into a properly capitalised title. It applies many small rules (small words, acronyms,
names, hyphenated and slashed words, punctuation, whitespace, ...), several of which
the original implements with regular expressions.

For reference while you work, `python3` with the `regex` package is installed in this
container, so you can run the original (`from titlecase import titlecase`) from
`/workspace/repo`. The reference behaviour is the one with the `regex` package
available. A Go 1.23 toolchain is installed; there is no network access.

## What to build

Replace the Python implementation with a Go program in `/workspace/repo`:

- The module root is `/workspace/repo` (it must contain a `go.mod`), and the `main`
  package is at the repository root, so `go build .` there produces the program.
- The program reads titles from standard input, one per line, and writes the titlecased
  result of each line to standard output, one per line, each terminated by `\n`.
- Input is valid UTF-8. No line contains `\r` or any other line-break character.

## Hard rules

1. Go standard library only: no third-party modules.
2. When you are finished, **no `.py` file may remain anywhere** in `/workspace/repo`
   (including in subdirectories and hidden directories).
3. `go build ./...` must succeed in `/workspace/repo`.

## Behaviour

For every input line, the output line must be **byte-for-byte identical** to what the
original `titlecase(line)` returns with its default arguments (no callback,
`small_first_last=True`, `preserve_blank_lines=False`,
`normalise_space_characters=False`), with the `regex` package available.

Titles consist of ASCII text, common punctuation (including curly quotes and the dash
characters), Latin-1 and Latin Extended-A letters, and the usual Unicode space
characters. You do not need to handle characters whose upper- or lower-case form is
more than one character long (for example `ß`) or that have context-dependent case
conversion.

## Not checked

Speed and memory (as long as a few thousand lines finish well within a minute), error
message wording, code style, and documentation.

## How it is graded

Hidden automatic tests produce a partial score from three things: whether the build
succeeds, whether any Python file remains, and what share of a set of hidden titles your
program titlecases exactly like the original.
