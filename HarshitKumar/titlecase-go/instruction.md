# What the repository is

The repository at `/workspace/repo` is the Python library python-titlecase. Its `titlecase()` function converts a line of text to title case.

# What to build

Build a Go program in `/workspace/repo` with a `go.mod` and a `main` package at the repository root. From `/workspace/repo`, `go build ./...` passes and `go run .` works.

The program reads UTF-8 text from stdin, one title per line. For each line it writes the result of the original Python `titlecase()` with its default options to stdout, one result per line, and each result ends in a newline. The default options are `callback=None`, `small_first_last=True`, `preserve_blank_lines=False`, and `normalise_space_characters=False`.

# Hard rules

Use only the Go standard library. No `.py` files may remain anywhere in the repository when you finish. `go build ./...` must pass.

# Behaviour

The output must match the original Python `titlecase()` byte for byte, for every input.

# Not checked

Speed, memory, and error message wording are not checked.

# How it is graded

Hidden automatic tests assign a partial score.
