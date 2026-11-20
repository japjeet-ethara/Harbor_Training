Work in `/workspace/repo`.

`go build ./...` must exit 0.

No file anywhere under `/workspace/repo` has a name ending in `.py`.

`go run .` reads stdin and writes stdout. Decode stdin as UTF-8. Split it with the same rules as Python `str.splitlines()`. For each line, in order, append the UTF-8 encoding of `titlecase(line)` and then `\n`. `titlecase` is the function defined in `titlecase/__init__.py`, called with that one argument and no other arguments. Stdout is those bytes and nothing else.
