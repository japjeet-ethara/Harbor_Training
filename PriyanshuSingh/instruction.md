# Port Python Titlecase to Go

## About the Repository

The repository at `/workspace/repo` contains python-titlecase version 2.4.1, an MIT-licensed Python library. Its `titlecase()` function, located in `titlecase/__init__.py`, converts a string into a headline-style title. It follows a series of rules to determine how words should be capitalized, such as keeping small words lowercase, preserving acronyms and mixed-case words, and handling some surnames specially.

## What Needs to Be Done

Replace the existing Python library with a Go program inside `/workspace/repo`.

The following requirements must be met:

- The `go.mod` file and `package main` must be located directly in `/workspace/repo`.
- Running `go build -o <path> .` from that directory must successfully build the program.
- The program must read UTF-8 text from standard input, processing one title per line.
- Input lines are separated by `\n` and do not contain `\r`.
- Each input line must be converted to title case, and its result must be printed on a separate output line.
- The output must preserve the original order of the input lines.
- The program must exit with status code 0.
- Empty input lines must produce empty output lines.

## Important Requirements

The implementation must follow these restrictions:

- Use only the Go standard library. Third-party modules and cgo are not allowed.
- Remove every `.py` file from `/workspace/repo`, including files in subdirectories.
- Make sure `go build ./...` completes successfully when run from `/workspace/repo`.
- The final program must be self-contained: it must run as an unprivileged user on a machine where Python is not installed.

## Expected Behaviour

For every input line, the Go program must produce exactly the same output as the original Python `titlecase(line)` function.

The comparison is byte-for-byte, so the output must match for all inputs, including text containing non-ASCII characters.

The reference implementation is the original `titlecase(line)` function running with its default arguments on CPython 3.12.

The optional `regex` package is not installed in the reference environment. Therefore, the original module uses Python's standard library `re` implementation.

## What Will Not Be Tested

Execution speed and memory consumption are not part of the evaluation.

The exact wording of error messages also does not matter.

The only performance requirement is that a single run processing a few thousand titles must finish within 120 seconds.

## How the Solution Will Be Evaluated

The solution will be evaluated through hidden automated tests after completion, and it can earn a partial score.

The grading is divided into three parts:

1. **Successful build:** Credit is awarded when `go build ./...` passes.
2. **Python file removal:** Credit is awarded when no `.py` files remain and the build also passes.
3. **Behavioural accuracy:** The largest portion of the score is the share of titles whose output exactly matches the original Python implementation.
