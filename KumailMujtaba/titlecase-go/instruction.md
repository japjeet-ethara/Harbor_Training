# Titlecase in Go

Done means every item below is true in `/workspace/repo`.

1. `go build ./...` exits 0.
2. No file under `/workspace/repo` has a name ending in `.py`.
3. `go run .` reads standard input one line at a time and writes one line per input line. Split input lines on `\n` and drop a trailing `\r`. For each line, call the Python `titlecase()` function from this repository with its default arguments on that line and write those exact bytes, followed by `\n`. Empty input produces empty output.
