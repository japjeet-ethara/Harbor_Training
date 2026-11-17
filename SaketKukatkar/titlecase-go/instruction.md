# Port python-titlecase to Go

`/workspace/repo` contains python-titlecase 2.4.1 (MIT licence), a pure-Python library. Its `titlecase()` function in `titlecase/__init__.py` converts a line of text to title case: it keeps small words such as "of" and "the" lowercase, leaves acronyms and mixed-case words such as "NASA" and "iPhone" alone, handles names such as "McDonald" and "O'Neill", and treats hyphens, slashes, abbreviations and web addresses specially.

## What to build

Replace the Python library with a Go program in `/workspace/repo`. It reads UTF-8 text from standard input, one title per line, and writes the title-cased result for each line to standard output, one per line, each terminated by `\n`. The program must be a `package main` at the repository root, with `go.mod` in `/workspace/repo`, so that `go build .` produces the executable.

## Hard rules

- Use only the Go standard library. No third-party modules. Do not use the network.
- `go.mod` must not require a Go version newer than 1.23 (the installed toolchain).
- `go build ./...` must pass from `/workspace/repo`. (Go names the executable after the module; if it reports that the output name already exists as a directory, give the module a different name.)
- When you finish, no file ending in `.py` may remain anywhere under `/workspace/repo`. The Python implementation, its tests and its packaging files must all be deleted; only the Go program remains.

## Behaviour

For every input line, the output line must be identical, byte for byte, to what the original `titlecase(line)` returns with default arguments (no callback, no word-list file, no other options), when the library runs with the optional `regex` package installed (the `REGEX_AVAILABLE = True` code path, which uses Unicode-aware patterns).

Input lines are non-empty, contain no `\r` or `\n`, and are made of ASCII characters, ordinary Latin and Cyrillic letters, punctuation, and whitespace (spaces, tabs and no-break spaces). Whitespace inside the line, including leading and trailing whitespace, must come out exactly as the original produces it. Characters with special case mappings (such as "ß") are not used.

Python's regular expressions use look-around and backtracking that Go's `regexp` package does not support, so each rule must be re-implemented with equivalent logic rather than copied.

## Not checked

Speed and memory (as long as a few thousand lines are processed within two minutes), error-message wording, and the names and layout of your source files.

## How it is graded

Hidden automatic tests run after you stop and give a partial score from three weighted checks: the build passes; no `.py` file remains (this check counts only if the build passes); and the share of hidden input lines whose output matches the original exactly. The third check carries the most weight. No test inputs or expected answers are available to you.
