# Port python-titlecase to Go

## Repository and reference behavior

The repository at `/workspace/repo` contains the MIT-licensed `ppannuto/python-titlecase` project, version 2.4.1, pinned to commit `42f43e2de55bf003b286c6f8e8d8b2d26676a167`. It formats text using context-sensitive small-word, capitalization, punctuation, acronym, apostrophe, slash, and hyphen rules.

Port the default `titlecase.titlecase(text)` function, as implemented by that source, to Go. The reference runtime is CPython 3.12 with Unicode 15.0.0 and Python's standard-library `re` fallback. The optional third-party `regex` package is absent. Use the function's default arguments, with no callback and no replacement small-word list. The reference function's actual behavior is authoritative, including behavior that differs from conventional title capitalization.

## Required program

Create a Go module and an executable main package at the repository root, `/workspace/repo`. Both `go build ./...` and `go build -o /tmp/titlecase .` must succeed, and `go run .` must expose the interface below.

Read UTF-8 titles from standard input, one record per LF-delimited line. Each record contains no embedded CR or LF; other Unicode characters and whitespace must be handled as the reference handles them. An empty input stream contains no records. A blank line contains one empty title. The final input record may omit its terminating LF.

For each input record, apply the equivalent of the reference function to the record without its LF delimiter. Print that result followed by exactly one LF. Emit exactly one output record per input record and no additional text on standard output. Output must match the reference bytes exactly, including spacing and Unicode case conversions. Support lines longer than 64 KiB; do not rely on the default scanner token limit.

## Implementation rules

Use Go's standard library only. Source files in the same Go module are allowed; third-party Go modules, vendored dependencies, non-Go transformation programs, and invoking an external interpreter to perform titlecasing are not allowed. Implement the transformation in Go rather than replaying a fixed list of outputs.

When finished, no files with a `.py` suffix may remain anywhere under `/workspace/repo`, including the upstream Python test files. Keep the upstream MIT license notice. Files outside `/workspace/repo` are not part of this removal requirement.

Do not modify the Go toolchain or system executables to alter compilation or grading behavior. Do not access grading resources or write reward files.

## Grading

Hidden automatic checks award partial credit using a weighted mean:

- **Build, weight 1:** the Go packages compile and use only the permitted dependencies.
- **No Python, weight 1:** the build criterion passes and no `.py` files remain in the repository.
- **Behavior, weight 4:** the share of input records whose complete output bytes match the reference, subject to successful build and execution and the required line protocol.

The total score is `(build + no_python + 4 * behavior) / 6`. A complete solution earns 1.0. A program that does not compile earns 0.0. Speed, memory use, code style, and error-message wording are not separately scored; executions must still finish within the task's operational time limits.
