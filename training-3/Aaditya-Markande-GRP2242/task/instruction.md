# Port python-titlecase to Go

## The repository
`/workspace/repo` contains python-titlecase 2.4.1 (MIT licence). Its `titlecase()` function in
`titlecase/__init__.py` turns a title into proper title case: small words such as "of" and "the"
stay lowercase, acronyms and words like "iPhone" are kept, hyphenated and slashed words are
handled part by part, and so on. Python 3 with the `regex` module is installed, so you can run
the original, for example:

    cd /workspace/repo && python3 -c "from titlecase import titlecase; print(titlecase('the lord of the rings'))"

## What to build
A Go program whose module root is `/workspace/repo` (`go.mod` in that folder, `package main` in
the same folder). It reads standard input one title per line and writes the titlecased result to
standard output, one result per line, each ending with a newline. Titles are single lines of
printable ASCII (spaces and tabs may appear between words). The program takes no arguments.

## Hard rules
1. Use the Go standard library only. No third-party modules.
2. When you finish, no file ending in `.py` may exist anywhere under `/workspace/repo`.
   Delete the original Python files after you have ported them.
3. `go build ./...` run in `/workspace/repo` must succeed.

## Behaviour
For every input line, your output must be identical, byte for byte, to what the original
`titlecase(line)` returns with its default options and the `regex` module installed.

## Not checked
Speed, memory use, error message wording, tests, documentation and code style.

## How it is graded
Hidden automatic tests give a partial score from 0 to 1. It combines: the build passing, no
`.py` files remaining, and the share of input lines whose output matches exactly (this part
counts the most).
