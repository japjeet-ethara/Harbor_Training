# Port python-titlecase to Go

## Repository

`/workspace/repo` holds the Python project python-titlecase, version 2.4.1 (MIT licence). Its function `titlecase()` in `/workspace/repo/titlecase/__init__.py` turns a line of text into title case: `the lord of the rings` becomes `The Lord of the Rings`.

## What to build

Replace the Python code with a Go program that does the same. The file `go.mod` and the main package are in `/workspace/repo` itself. The program reads titles from standard input, one title per line, encoded as UTF-8. For each input line it writes one line to standard output: the title-cased form of that line, followed by one newline character. The order of the lines is kept.

## Hard rules

- Use the Go standard library only. The build is run offline with the Go 1.23 toolchain that is in the container, so a module that has to be downloaded does not build.
- `go build ./...`, run in `/workspace/repo`, must pass.
- At the end, no file whose name ends in `.py` exists anywhere under `/workspace/repo`.

## Behaviour

For every input line, the output line must equal, byte for byte, what `titlecase(line)` of the original returns with its default arguments, on the code path it takes when the optional `regex` package is not installed (`REGEX_AVAILABLE` is `False`).

Input lines contain only printable ASCII characters, tabs, the curly quotes U+2018, U+2019, U+201C and U+201D, and the dashes U+2012, U+2013, U+2014 and U+2015.

## Not checked

Memory use, the wording of error messages, and speed, except that a run over a few thousand lines must finish within two minutes.

## Grading

Hidden automatic tests give a partial score from three things: whether the build passes, whether no `.py` file is left (counted only when the build passes), and the share of test lines whose output is exactly right. The last one counts four times as much as each of the others.
