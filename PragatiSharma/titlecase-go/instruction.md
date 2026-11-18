# Titlecase in Go

## Repository overview

`/workspace/repo` is a checkout of python-titlecase, an MIT-licensed Python port of John Gruber’s titlecase.pl. The titlecasing rules live in `titlecase/__init__.py`. `NOTES.md` summarizes them.

## What to build

Replace this project with a Go command-line program whose module root and `main` package are `/workspace/repo`. The program reads one title per line from standard input and writes that title’s titlecased result to standard output, one per line, including empty lines. Remove the input line ending (`\n` or `\r\n`) before calling the equivalent of `titlecase()`. Pass every other input character through the original titlecasing behavior. Write each result followed by `\n`. Do not implement the Python tool’s flags, abbreviation file, or callback.

## Hard rules

- Use only the Go standard library.
- Leave no `.py` files anywhere under `/workspace/repo`.
- `go build ./...` must succeed when run from `/workspace/repo`.

## Required behavior

For each input title, produce exactly the same output, byte for byte, as the original Python `titlecase()` function in this checkout, called with its default arguments. Read the original source before removing the Python files. The reference outputs will be generated using Python’s standard-library `re` implementation, without the optional third-party `regex` package.

## Not graded

Speed, memory usage, and error-message wording are not graded.

## Grading

Hidden automatic tests grade the program. Partial credit is awarded.
