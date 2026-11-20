# Port python-titlecase to Go

`/workspace/repo` is a checkout of [python-titlecase](https://github.com/ppannuto/python-titlecase) (MIT), a Python library whose `titlecase()` function converts a string to title case. Its source, including `titlecase/__init__.py`, is in the repo.

Replace that Python project with a Go program. The `go.mod` file and the `main` package must be directly in `/workspace/repo`, so that `go build .` there produces the program.

The program reads ASCII text from standard input, one title per line, and writes one output line per input line, each ending in `\n`. Each output line must be byte for byte what the original Python `titlecase(line)` returns, called with no other arguments, where `line` is the input line without its trailing newline.

Rules:

- Use only the Go standard library (`go.mod` must have no `require` lines).
- Do not leave any `.py` file anywhere under `/workspace/repo`.
- `go build ./...` run in `/workspace/repo` must succeed.

Speed, memory use, and error message wording are not graded.

Grading is automatic and hidden. It checks the build, the absence of `.py` files, and the share of test lines whose output matches exactly. A partial match gets a partial score.