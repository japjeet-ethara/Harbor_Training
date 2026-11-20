# Port `python-titlecase` to Go

## 1. The repository

`/workspace/repo` contains **python-titlecase** 2.4.1 (MIT licence), a small Python library whose
`titlecase()` function turns a line of text into a properly capitalised title, for example
`the lord of the rings` becomes `The Lord of the Rings`. It applies many special rules (small words
such as "of" and "the", acronyms, web links, apostrophes, hyphens, slashes and more). The code is in
`titlecase/__init__.py`.

## 2. What to build

Write a Go program in `/workspace/repo` that reads titles from standard input, one per line, and
writes the titlecased result to standard output, one line per input line, in the same order.

- `go.mod` is at the root of `/workspace/repo` and the program is the `main` package in that same
  root directory, so that `go build .` run there produces the executable.
- Input lines end with `\n`. A line never contains `\r`. A line may be empty, or may contain only
  spaces or tabs. Every input line produces exactly one output line.

## 3. Hard rules

- Go standard library only: no third-party modules.
- No `.py` files may remain anywhere under `/workspace/repo` when you finish.
- `go build ./...` must pass in `/workspace/repo` (the check is that everything compiles and that the root directory is a `main` package; it is run as `go build -o /dev/null ./...`, so the output binary's name does not matter).

## 4. Behaviour

For every input line, the output line must be identical, byte for byte, to what the original Python
`titlecase(line)` returns with its default arguments. The reference is python-titlecase 2.4.1 as
provided in the repository, running on Python's standard-library `re` module (the optional `regex`
package is not installed). Input and output are UTF-8.

## 5. Not checked

Speed, memory use, code style, error-message wording, and any behaviour for command-line arguments
or for options other than the defaults of `titlecase()`.

## 6. How it is graded

Hidden automatic tests run after you finish and give a partial score between 0 and 1, a weighted
average of three checks:

| Check | Weight | Passes (scores 1) when |
|---|---|---|
| build | 1 | everything compiles: `go build ./...` succeeds in `/workspace/repo` and its root is a `main` package |
| no_python | 1 | there are no `.py` files under `/workspace/repo` and the build succeeds |
| behaviour | 4 | the program is fed a large hidden set of titles; the score is the share of output lines that exactly match the Python output |
