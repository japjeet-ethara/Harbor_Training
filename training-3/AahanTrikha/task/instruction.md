# Port python-titlecase to Go

## The repository
`/workspace/repo` contains python-titlecase, a Python library that title-cases text
following the New York Times Manual of Style. Its behaviour is defined by
`titlecase/__init__.py`.

## What to build
A Go program at the root of `/workspace/repo` (package main) that reads one title
per line from stdin and writes the title-cased result to stdout, one output line
per input line.

## Hard rules
- Go standard library only. No third-party modules.
- `go build ./...` must succeed in `/workspace/repo`.
- No `.py` files may remain anywhere under `/workspace/repo`.

## Behaviour
Output must match the original Python `titlecase()` byte for byte for every input,
including unicode characters, apostrophe names, Mc/Mac handling, hyphen and slash
splitting, and words that must be left untouched such as URLs and mixed-case names.
Go's regexp has no look-ahead, look-behind or back-references; reproduce the
behaviour with plain string inspection where needed.

## Not graded
Speed, memory use, wording of error messages.

## Grading
Hidden automatic tests feed unseen inputs to your program and compare each output
line against the reference Python output. Partial credit is given.