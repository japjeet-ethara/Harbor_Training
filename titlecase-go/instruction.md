# Titlecase in Go

Done means all three of the following are true.

## Build

`/workspace/repo` contains a Go main package in that directory. From `/workspace/repo`, `go build ./...` exits 0. The program built there reads stdin and writes stdout.

## No Python files

No file whose name ends in `.py` remains anywhere under `/workspace/repo`.

## Exact output

Split stdin on `\n` into lines, keeping a final empty line when the input ends with `\n`. Drop the line delimiter. For each line, in order, write exactly the bytes returned by this repository's Python `titlecase()` called on that line with its default arguments, then one `\n`.
