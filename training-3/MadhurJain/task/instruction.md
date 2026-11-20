## What the repository is

/workspace/repo contains https://github.com/ppannuto/python-titlecase at commit 42f43e2de55bf003b286c6f8e8d8b2d26676a167 (2024-04-05T22:03:59-07:00), under the MIT License. Its `titlecase` function title-cases text one line at a time.

## What to build

Build a Go program in `/workspace/repo` whose main package is at the repository root, so `go build -o titlecase .` builds it. It reads UTF-8 text from standard input, one title per line, and prints one output line per input line, each ending in a newline. Titles are never empty, but they may contain tabs, non-breaking and other Unicode spaces, punctuation, digits and letters from any script.

## Hard rules

- Use the Go standard library only: `go.mod` has no `require` lines and there is no `vendor/` folder.
- `go.mod` declares Go 1.23 or lower. The container has Go 1.23.
- `go build ./...` must compile.
- No `.py` files may be left anywhere under `/workspace/repo`.

## Behaviour

Answers come from titlecase WITHOUT the optional `regex` package. Each output line must match, byte for byte, `titlecase(line)` from the original code, called with default arguments, on Python 3.14 using Python's built-in `re` module.

The program is graded on its own: it is built with `CGO_ENABLED=0`, then run in an empty folder as an unprivileged user, with no other files or programs available (no Python, no test data, no repository). Everything it needs must be inside the binary.

## Not checked

Speed, memory, code style, and error message wording are not checked.

## How it is graded

Hidden automatic tests on 100,000 titles award a partial score:

- build (1 point): the hard rules above hold and the program builds.
- behaviour (4 points): the share of titles answered exactly right. Below 90% right earns nothing; from 90% it rises evenly to full marks at 100%.
- no_python (1 point): no `.py` file is left, counted only when behaviour earns points.
