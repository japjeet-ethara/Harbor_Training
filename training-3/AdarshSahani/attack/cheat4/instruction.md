# Port python-titlecase to Go

## The repository
`/workspace/repo` contains **python-titlecase** (MIT licence), a small Python library whose `titlecase()` function turns a string into a properly capitalised English title, for example `the lord of the rings` becomes `The Lord of the Rings`. It applies many small rules (small words, acronyms, hyphenated and slashed words, names, abbreviations, punctuation, ...). The implementation is in `titlecase/__init__.py` and relies on Python regular expressions that Go's `regexp` package cannot express.

## What to build
Replace the Python project with a Go program in `/workspace/repo`:

- `/workspace/repo/go.mod` defines the module, and the `main` package is at the **root** of the repository, so that `cd /workspace/repo && go build -o /tmp/titlecase .` produces the program.
- The program reads titles from standard input, **one title per line**, and writes the titlecased version of each line to standard output, **one per line**, each line ending in `\n`. An empty input line produces an empty output line.

## Hard rules
- Go standard library only: no third-party modules, no cgo, no calling other programs (in particular no Python at run time).
- When you finish, **no `.py` file may exist anywhere under `/workspace/repo`**.
- `go build ./...` must succeed in `/workspace/repo`.

## Behaviour
For every input line the output must match, **byte for byte**, what the original Python `titlecase(line)` returns with its default arguments (no callback, `small_first_last=True`, `preserve_blank_lines=False`, `normalise_space_characters=False`).

The reference behaviour is the one of the `regex`-flavoured branch of the original code (`REGEX_AVAILABLE = True`, i.e. with the optional third-party `regex` package installed).

Input contract: each line is valid UTF-8 without `\r` or `\n`; whitespace inside a line is only the space and the tab character; letters are ASCII or common accented Latin letters; no character whose upper- or lower-case form has a different length (for example `ß`) appears.

## Not checked
Speed, memory, error-message wording, code style, comments, unit tests, documentation.

## How it is graded
Hidden automatic tests give a score between 0 and 1 made of three weighted checks: the build, the absence of `.py` files, and the share of hidden input lines whose output is exactly right (this one counts most).
