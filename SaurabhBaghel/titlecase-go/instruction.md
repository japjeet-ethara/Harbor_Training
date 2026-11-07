# Port python-titlecase to Go

`/workspace/repo` is the python-titlecase 2.4.1 source tree (MIT). The function to preserve is `titlecase()` in `titlecase/__init__.py`. This container has Python 3 and the third-party `regex` package installed, so importing `titlecase` sets `REGEX_AVAILABLE = True` and uses that branch. Do not uninstall `regex` and do not rely on the stdlib `re` fallback.

## What to build

Replace the Python implementation with a Go program whose module root is `/workspace/repo`.

- `go build ./...` must succeed.
- `CGO_ENABLED=0 go build -o titlecase .` must succeed and produce the program that is graded. Use only the Go standard library. Do not use cgo or packages outside the standard library.
- The program reads UTF-8 from stdin, one title per line, and writes one title per line to stdout using `\n` line endings.
- For each input line, not including its trailing newline, the corresponding output line must be exactly the bytes returned by `titlecase(line)` called with the default arguments: `callback=None`, `small_first_last=True`, `preserve_blank_lines=False`, and `normalise_space_characters=False`.
- Delete every `.py` file under `/workspace/repo`. None may remain anywhere in the repository.

While the Python sources are still present you can execute the original function with `python3` and compare its output to the Go program.

## Not graded

Speed, memory use, and the wording of error output are not graded.

## Grading

Hidden checks score three things and combine them as a weighted mean: a successful `go build ./...` (weight 1), no `.py` files left and a successful build (weight 1), and the fraction of hidden lines whose output matches `titlecase()` exactly (weight 4). A partial solution receives partial credit.
