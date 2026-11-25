# Repository

`/workspace/repo` contains the Python project python-titlecase (MIT licence, commit `42f43e2de55bf003b286c6f8e8d8b2d26676a167`). Its `titlecase()` function converts a line of text to title case. The reference is the existing pinned Python titlecase source running under Python 3.14.10 with standard-library re, without the optional regex package.

# Task

Replace the Python implementation with a Go program in `/workspace/repo`.

- `go.mod` is in `/workspace/repo`. The main package is in `/workspace/repo` itself. The verifier runs `go build -o <path> .` there.
- The program reads UTF-8 lines from stdin. For each input line, it writes the result of `titlecase(line)` with default arguments to stdout, followed by a single `\n`.
- An empty input line produces an empty output line.

# Input

Each input line contains only printable ASCII characters (space to `~`), tab, and these characters: ‘ ’ “ ” – —, U+00A0, ç (U+00E7), ö (U+00F6), ü (U+00FC), İ (U+0130), ı (U+0131), and ş (U+015F), plus U+00C9, U+00CF, U+00DC, U+00DF, U+00E9, U+00EF, U+0391, U+03B1, U+0414, U+041C, U+041E, U+0434, U+043C, U+043E, and U+2009. Lines contain no `\r` or `\n`. Input always ends with a final `\n`. The observed 105-byte maximum is not an input limit.

# Required behaviour

For every input line, the output must be byte-for-byte identical to the original Python `titlecase()` called with default arguments on that line. The program must process 100,000 titles in one invocation with a 60-second execution limit.

# Hard rules

- Use the Go standard library only.
- `go build ./...` must succeed in `/workspace/repo`.
- No `.py` files may exist anywhere under `/workspace/repo` when you finish.
- The Go program must not run any other program or interpreter (no `os/exec`, no Python). The Go program must read only stdin at runtime.
- Do not download code or data from the internet.

# Not scored

Memory use and error-message wording are not scored.

# Grading

Hidden automatic checks cover the build, the absence of `.py` files (no_python), and the output on a hidden set of lines (behaviour). The build and no_python checks are strict prerequisites: if either `build` or `no_python` fails, the final reward is `0.0`. When both pass (`build == 1` and `no_python == 1`), the final reward is the square of the byte-exact behaviour score ($\text{reward} = \text{behaviour}^2$). The score is partial (between 0 and 1).
