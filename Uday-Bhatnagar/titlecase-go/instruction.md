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

## Not checked
Speed, memory use, and the wording of error messages.

## How it is graded
Hidden automatic tests give a partial score. Whether the code builds, whether
any Python files remain, and the share of input lines whose output matches the
original exactly are each scored, and matching the original's output counts for
the most.