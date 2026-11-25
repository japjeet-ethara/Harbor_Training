# Port `titlecase` from Python to Go

## 1. What the repository is

`/workspace/repo` contains `python-titlecase` version 2.4.1, an MIT-licensed Python library. Its main function, `titlecase()` in `titlecase/__init__.py`, converts text to title case.

## 2. What to build

Build a Go program in `/workspace/repo` that reads one title per line from stdin and prints the titlecased result, one per line.

- Put the `main` package at the repository root, with a `go.mod` file there, so that `go run .` from `/workspace/repo` runs the program.
- Input is UTF-8 text. Split stdin on `\n` only. A final `\n` does not start another line, and a last line without a `\n` still counts as a line. Empty stdin produces no output.
- For each line, in order, print the result of `titlecase(line)` with default arguments, followed by `\n`. Print the result unchanged, even if it contains a `\n` of its own.

## 3. Hard rules

- Use the Go standard library only.
- Leave no `.py` files anywhere in the repository when you finish.
- `go build ./...` must pass from `/workspace/repo`.

## 4. Behaviour

The output must match the original Python `titlecase()` byte for byte, for every input.

The reference is the code as it runs in this environment: `python3` (3.11) with only the standard library. The optional `regex` package is not installed, so the original uses its fallback to Python's built-in `re` module.

## 5. Not checked

- Speed
- Memory use
- Error message wording

## 6. How it is graded

Your work is graded by hidden automatic tests, with a partial score.
