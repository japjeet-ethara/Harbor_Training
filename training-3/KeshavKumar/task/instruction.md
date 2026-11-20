# Port python-titlecase to Go

## The repository

`/workspace/repo` contains python-titlecase 2.4.1, a Python library. Its `titlecase(text)`
function (in `titlecase/__init__.py`) converts text to Title Case using New York Times
style rules. Small words such as "a", "of" and "the" stay lowercase except at the start or
end of a title or after a colon. Acronyms, domain names, mixed-case words ("iPhone"),
Mc-names ("McDonald"), d'/o'/l'-names ("O'Neil") and hyphenated or slashed words are
handled specially.

## What to build

Replace the Python library with a Go program in `/workspace/repo`:

- `/workspace/repo/go.mod` declares the module, and the package in `/workspace/repo`
  itself is `package main`. The grader builds the program by running
  `go build -o <path> .` in `/workspace/repo`.
- The program takes no command-line arguments. It reads UTF-8 text from standard input,
  where lines are separated by `\n`. For each line it writes the titlecased line followed
  by `\n` to standard output, in the same order. A last line without a trailing `\n` is
  also processed.
- Input lines never contain `\r`.

## Hard rules

1. Go standard library only: `go.mod` contains no `require` directives.
2. No file ending in `.py` may remain anywhere under `/workspace/repo`.
3. `go build ./...` run in `/workspace/repo` must succeed.

## Required behaviour

For every input line `L`, the output line must be byte-for-byte identical to the string
the original Python code returns for `titlecase(L)`, where:

- `titlecase` is called with default arguments only (no callback, no wordlist file);
- the code runs on Python 3 with the standard-library `re` module, i.e. as it behaves
  when the optional third-party `regex` module is not installed.

## Not checked

Speed, memory use, code style, and the wording of error messages.

## Grading

Hidden automatic tests produce a partial score from 0 to 1, as a weighted mean of:

| Check | Weight | Scores 1 when |
|-------|--------|---------------|
| build | 1 | `go.mod` has no `require` directives and `go build ./...` succeeds in `/workspace/repo` |
| no_python | 1 | no `.py` file exists under `/workspace/repo`, the build succeeds, **and** at least half of the hidden input lines match exactly |
| behaviour | 4 | fraction of hidden input lines whose output line matches exactly (0 to 1) |
