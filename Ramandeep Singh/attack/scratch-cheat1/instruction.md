# Port python-titlecase to Go

## The repository

`/workspace/repo` contains **python-titlecase** (MIT licence), a small Python library whose main function, `titlecase()` in `titlecase/__init__.py`, turns a string such as `the lord of the rings` into a title such as `The Lord of the Rings`. It has many special-case rules (small words, acronyms, hyphenated and slashed words, `Mc` names, apostrophes, sub-phrases, Unicode letters, and more).

## What to build

Replace the Python implementation with a Go program that lives in `/workspace/repo`:

- `/workspace/repo/go.mod` must exist, and the repository root must be a `main` package, so that `go build .` produces the program.
- The program reads titles from standard input, **one title per line**, and writes the titlecased result to standard output, **one result per line**, each terminated by `\n`. N input lines produce exactly N output lines (an empty input line produces an empty output line).
- Each input line is titlecased independently, exactly as the original `titlecase(line)` would do with its **default arguments** (no callback, no wordlist, `small_first_last=True`, `preserve_blank_lines=False`, `normalise_space_characters=False`).
- The reference behaviour is the code path used when the optional third-party `regex` package **is** installed (`REGEX_AVAILABLE = True`), so Unicode letters are handled as letters.

## Hard rules

1. Use the Go standard library only. `go.mod` must not list any dependency.
2. When you are done, there must be **no file ending in `.py` anywhere** under `/workspace/repo` (including subfolders and hidden folders).
3. `go build ./...` must succeed in `/workspace/repo`.

## Behaviour

For every input line, the output line must be identical to the output of the original Python `titlecase()`, byte for byte. This includes whitespace, punctuation, and non-ASCII letters, not only the common cases.

## Not checked

Speed, memory use, source code style, and the wording of any error or log message.

## How it is graded

Hidden automatic checks run after you finish. The score is a number from 0.0 to 1.0 made of partial credit: whether the project builds, whether the Python files are gone, and (with the largest weight) the share of hidden input lines for which your program's output is exactly correct.
