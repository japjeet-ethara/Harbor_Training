## What the repository is

/workspace/repo contains https://github.com/ppannuto/python-titlecase at commit 42f43e2de55bf003b286c6f8e8d8b2d26676a167 (2024-04-05T22:03:59-07:00), under the MIT License. Its `titlecase` function title-cases text one line at a time.

## What to build

Build a Go program in `/workspace/repo` whose main package is at the repository root, so `go build -o titlecase .` builds it. It reads UTF-8 text from standard input, one title per line (no blank lines), and prints one output line per input line, each ending in a newline.

## Hard rules

- Use the Go standard library only.
- `go.mod` declares Go 1.23 or lower. The container has Go 1.23.
- `go build ./...` must compile.
- No `.py` files may be left anywhere under `/workspace/repo`.

## Behaviour

Each output line must match, byte for byte, `titlecase(line)` from the original code, called with default arguments, on Python 3.12 without the optional `regex` package installed.

## Not checked

Speed, memory, code style, and error message wording are not checked.

## How it is graded

Hidden automatic tests award a partial score.
