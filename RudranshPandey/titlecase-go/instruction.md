# Titlecase in Go

## Repository Context
The repository in `/workspace/repo` contains `python-titlecase`, a Python library that capitalizes words in text according to title casing rules while preserving lowercase for small words, retaining capitalized acronyms and mixed-case terms, leaving URLs intact, and handling special punctuation and prefixes.

## Task
Port the titlecasing functionality to a Go program in `/workspace/repo`.
The Go program must read input titles line-by-line from standard input (`stdin`) and write the titlecased result for each line to standard output (`stdout`), terminated by a newline (`\n`).

## Requirements
- The Go program must build successfully using `go build ./...` executed in `/workspace/repo`.
- The Go implementation must use the Go standard library only; no external Go modules or dependencies are allowed.
- No `.py` files may remain anywhere in `/workspace/repo`.
- For each line read from stdin, the printed output must match the exact byte-for-byte output of the original Python `titlecase.titlecase()` function.

## Constraints and Evaluation
- Execution speed, memory usage, and error message wording are not evaluated.
- Submissions are evaluated automatically against hidden test inputs and receive partial credit based on build success, absence of `.py` files, and the proportion of test titles matching the expected titlecased output exactly.

