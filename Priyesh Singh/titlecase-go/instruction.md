The repository in `/workspace/repo` is python-titlecase 2.4.1, a Python port of John Gruber's title-case filter. Its `titlecase()` function rewrites a title using a fixed set of rules: small words stay lowercase except at the start or end of a title and after certain punctuation, while names, initials, acronyms, apostrophes, hyphens, slashes, and URLs follow the behaviour already implemented in this tree. The optional `regex` package is not part of the default install; match the behaviour of the code path that uses the Python standard-library `re` module, with the function's default arguments.

Replace that program with a Go program in `/workspace/repo`. It must read one title per line from standard input and write the title-cased line to standard output, one line per input line. Build it with the Go standard library only.

These are required:

- `go build ./...` succeeds in `/workspace/repo`.
- No `.py` file remains anywhere under `/workspace/repo`.
- For every input line, the output line matches `titlecase()` byte for byte.

Speed, memory use, and the wording of error messages are not graded. Hidden tests award partial credit.
