# Titlecase in Go

## 1. What the repository is

`/workspace/repo` is the Python package [python-titlecase](https://github.com/ppannuto/python-titlecase) at commit `42f43e2de55bf003b286c6f8e8d8b2d26676a167` (2024-04-05T22:03:59-07:00), under The MIT License (MIT). Its `titlecase` function rewrites text into title caps. Ordinary words are capitalized. A fixed list of small words (`a`, `an`, `and`, `as`, `at`, `but`, `by`, `en`, `for`, `if`, `in`, `of`, `on`, `or`, `the`, `to`, `v`, `v.`, `via`, `vs`, `vs.`, from the New York Times Manual of Style plus `v` and `vs`) is lowercased, then capitalized again at the start or end of a line and after a subphrase break. Further rules cover per-line processing, collapsed blank lines, preserved whitespace, callbacks, all-caps initials, `d`/`o`/`l` apostrophes, `Mc`/`MC`, `Mr`/`Mrs`/`Ms`/`Dr`, internal periods, existing interior capitals, single slashes, hyphens, all-caps lines, and all-consonant acronyms. The full rules are in `NOTES.md`.

## 2. What to build

Replace this package with a Go program in `/workspace/repo`. The program reads one title per line from stdin and prints the titlecased result, one per line.

## 3. Hard rules

- Use the Go standard library only.
- No `.py` files may be left anywhere in the repository.
- `go build ./...` must pass.

## 4. Behaviour

For every input, the output must match the original Python `titlecase()` byte for byte. Read that function and `NOTES.md` before removing the Python sources; the finished program has to reproduce `titlecase()` with its default arguments.

## 5. Not checked

Speed, memory, and error-message wording are not checked.

## 6. How it is graded

Hidden automatic tests score the program. A partial score is possible.
