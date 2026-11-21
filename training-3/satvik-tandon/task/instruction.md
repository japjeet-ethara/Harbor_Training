## Repository

This workspace contains the MIT-licensed `python-titlecase` project at commit
`42f43e2de55bf003b286c6f8e8d8b2d26676a167`. Its `titlecase()` function
implements title casing with rules for small words, acronyms, punctuation,
hyphens, slashes, apostrophes, names beginning with Mc/Mac, and existing mixed
capitalisation.

## Build

Replace the Python implementation with a Go program in `/workspace/repo`. The
program must read one title per line from standard input and print one
title-cased result per line to standard output.

## Requirements

- Use only the Go standard library.
- Remove every `.py` file from `/workspace/repo`.
- `go build ./...` must succeed in `/workspace/repo`.
- For every input title, the output must match the original Python
  `titlecase()` output byte for byte.

## Grading

The 100,000 hidden answers come from Python 3.14's built-in `re` mode,
with the optional `regex` package disabled. A successful build and removal of
Python source files are prerequisites. The verifier also checks the full Go
dependency list for third-party packages. The same 100,000 titles may be sent
in a different order on each grading run. Each input must produce one output line.
The reward is the number of exact answers divided by the total number of
inputs. The static Go binary runs as an
unprivileged user with the input stream, its own executable, and no network.
