# Port python-titlecase to Go

## The repository
/workspace/repo contains python-titlecase, a Python library whose `titlecase()`
function converts a string to title case using publishing-style rules: small
words stay lowercase, acronyms and mixed-case words are preserved, URLs and
similar tokens are left untouched, and so on.

## What to build
Write a Go program in /workspace/repo. The `main` package must be at the
repository root, with a `go.mod` there. The program reads UTF-8 text from
standard input, one title per line, and writes the titlecased result to
standard output, one line per input line, in the same order.

## Hard rules
- Use the Go standard library only. No third-party modules.
- When you finish, no `.py` file may exist anywhere under /workspace/repo.
  The Python implementation must be replaced, not kept alongside.
- `go build ./...` must pass from /workspace/repo.

## Behaviour
For every input line, your output must match the original Python
`titlecase()` function, called with its default arguments, byte for byte.
The reference is python-titlecase 2.4.1 without the optional `regex` package
(the standard-library `re` mode).

## Not checked
Speed, memory use, and the wording of error messages.

## How it is graded
The Go build and removal of Python source are required for any credit. The
verifier checks a frozen 100,000-title exam, the original regression cases,
and fresh titles generated for each run. The score is the lowest exact-match
rate across the three sets. Full credit requires every answer to match. The
executable runs with standard input and output in an isolated filesystem
without the workspace, reference, or exam files.
