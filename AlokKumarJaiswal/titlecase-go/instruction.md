# Repository

`/workspace/repo` contains the Python project python-titlecase (MIT licence, commit `42f43e2de55bf003b286c6f8e8d8b2d26676a167`). Its `titlecase()` function converts a line of text to title case. The Python source there is the reference behaviour.

# Task

Replace the Python implementation with a Go program in `/workspace/repo`.

- `go.mod` is in `/workspace/repo`. The main package is in `/workspace/repo` itself. The verifier runs `go build -o <path> .` there.
- The program reads UTF-8 lines from stdin. For each input line, it writes the result of `titlecase(line)` with default arguments to stdout, followed by a single `\n`.
- An empty input line produces an empty output line.

# Input

Each input line contains only printable ASCII characters (space to `~`), tab, and these characters: ‘ ’ “ ” – —. Lines contain no `\r` or `\n`. Input always ends with a final `\n`.

# Required behaviour

For every input line, the output must be byte-for-byte identical to the original Python `titlecase()` called with default arguments on that line.

# Hard rules

- Use the Go standard library only.
- `go build ./...` must succeed in `/workspace/repo`.
- No `.py` files may exist anywhere under `/workspace/repo` when you finish.
- The Go program must not run any other program or interpreter (no `os/exec`, no Python). The Go program must read only stdin at runtime.
- Do not download code or data from the internet.

# Not scored

Memory use and error-message wording are not scored. The program must process 2000 lines in under 60 seconds.

# Grading

Hidden automatic checks cover the build, the absence of `.py` files, and the output on a hidden set of lines. The score is partial (between 0 and 1).
