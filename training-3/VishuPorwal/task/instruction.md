# Titlecase in Go

## What the repository is

This repository is the Python `titlecase` package (MIT License). Its `titlecase` function walks text line by line and word by word, capitalising words while lowercasing a fixed set of small words from the New York Times Manual of Style, plus `v` and `vs`. Earlier rules win. They cover blank lines, optional callbacks, initials, `d`/`o`/`l` apostrophes, `Mc` prefixes, `Mr`/`Mrs`/`Ms`/`Dr`, internal periods, existing interior capitals, slashes, hyphens, all-caps lines, long all-consonant acronyms, first and last small words, sub-phrases, and original spacing unless space normalisation is requested.

## What to build

Replace that library with a Go program in `/workspace/repo`. The program reads one title per line from stdin and writes the titlecased result to stdout, one per line. The main package is the module root, so `go build -o titlecase .` from `/workspace/repo` produces the program.

## Hard rules

- Use the Go standard library only.
- No `.py` files may remain anywhere in the repository.
- `go build ./...` must pass.

## Behaviour

For every input line, the printed result must equal the original Python `titlecase()` of that line, byte for byte, using the function's default arguments. Write one result per line.

## Not checked

Speed, memory, and error message wording are not checked.

## Grading

Hidden automatic tests grade the program. Partial scores are possible.
