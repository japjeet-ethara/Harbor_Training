# Port python-titlecase to Go

## The repository

`/workspace/repo` contains https://github.com/ppannuto/python-titlecase at commit
`42f43e2de55bf003b286c6f8e8d8b2d26676a167` (MIT licence). It is a Python library
whose `titlecase()` function turns a line of text into a title, for example
`the lord of the rings` becomes `The Lord of the Rings`. It applies many small
rules: small words such as "of" and "the" stay lower case except at the start
and end, all-consonant words become upper case, words that already contain
inner capitals or inner periods are left alone, and so on. All of its logic is
in `titlecase/__init__.py`.

## What to build

Replace the Python program with a Go program in `/workspace/repo`:

- The program is the main package at the root of `/workspace/repo`: it is built
  with `go build -o <some path outside the repo> .` from that folder.
- The program reads UTF-8 text from standard input, one title per line.
- For every input line it prints exactly one output line: the result of the
  original Python `titlecase(line)` for that line, followed by `\n`.

## Hard rules

- Use the Go standard library only: `go.mod` must have no `require` lines.
  `go.mod` must allow Go 1.23 (the Go version installed here). There is no
  internet access.
- Every package in `/workspace/repo` must compile: `go build -o <a temporary folder>/ ./...`
  must pass.
- When you are done, no `.py` files may be left anywhere under `/workspace/repo`.

## Behaviour

The output must match the original Python `titlecase()` (run with Python 3 and
the `regex` package installed, which this environment has) byte for byte, for
every input line. Input lines contain no line breaks; they use printable ASCII,
the Latin-1 letters `À`–`ÿ`, and punctuation such as `“ ‘ ’ ” – ‒ — ― « » ¿ ¡`.

Go's `regexp` package has no look-ahead, look-behind or back-references, so the
Python regular expressions cannot all be copied across unchanged.

`/workspace/examples/inputs.txt` holds 2000 example titles and
`/workspace/examples/expected.txt` holds the correct output for each one, line
by line. You can also run the original Python code to check any input while
the `.py` files still exist.

## Not checked

Speed, memory use, code style, and the wording of error messages.

## How it is graded

Hidden automatic tests, with partial credit. They check that the build passes
with no third-party modules, that no `.py` files are left, and how many of a
separate, unseen set of titles your program titlecases exactly right.
