# Port python-titlecase to Go

## The repository
`/workspace/repo` contains python-titlecase, a Python library that title-cases text
following the New York Times Manual of Style. Its behaviour is defined by
`titlecase/__init__.py`. The container has **no Python interpreter** and **no network**;
read the source and port it by hand.

## What to build
A Go program at the root of `/workspace/repo` (package main) that reads one title
per line from stdin and writes the title-cased result to stdout, one output line
per input line.

## Hard rules
- Go standard library only. No third-party modules.
- `go build ./...` must succeed in `/workspace/repo`.
- No `.py` files may remain anywhere under `/workspace/repo`.

## Behaviour and answer mode
Output must match the original Python `titlecase()` byte for byte for every input,
including unicode characters, apostrophe names, Mc/Mac handling, hyphen and slash
splitting, and words that must be left untouched such as URLs and mixed-case names.
**The hidden answers come from `titlecase` WITH the optional `regex` package installed**
(the source calls this the `regex` engine; `REGEX_AVAILABLE` is true). Go's regexp has
no look-ahead, look-behind or back-references; reproduce the behaviour with plain
string inspection where needed.

## Not graded
Speed, memory use, wording of error messages.

## Grading
Hidden automatic tests feed unseen inputs to your program and compare each output
line with the reference. The reference answers are stored only as SHA-256 hashes.
`build` and `no_python` are prerequisites, not separate credit: if either fails the
reward is 0. Otherwise `reward = behaviour` (the exact fraction of matching lines).
