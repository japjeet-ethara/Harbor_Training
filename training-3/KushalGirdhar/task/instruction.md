# Port python-titlecase to Go

The Python source in `/workspace/repo` implements a title-casing function with rules for small words, acronyms, punctuation, names, compounds, and Unicode. Its default `titlecase(text)` behavior using CPython 3.12.14, Unicode 15.0.0, and the standard-library `re` backend is the reference.

Place a Go module with a root `main` package in `/workspace/repo`. Use only the Go standard library. Both `go build ./...` and `go build -o /tmp/titlecase .` must work from that directory. Remove every `.py` file within the repository, including in subdirectories. Keep your submission in regular files and directories.

Read UTF-8 titles from stdin, one record per LF or CRLF line. Treat an unterminated final record as a title and preserve empty records. A trailing LF completes the preceding record. For each record, write the bytes returned by the default Python function on the record content, then one LF. Preserve whitespace and punctuation according to the reference. Write only results to stdout.

Hidden automatic checks award partial credit for buildability, Python file removal after a passing build, and byte-exact behavior. The behavioral score uses the share of matching records in a correctly framed output stream.

Execution has infrastructure limits. Speed, memory use, and error wording are outside the scoring criteria.
