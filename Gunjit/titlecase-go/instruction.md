# Port python-titlecase to Go

## The repository

`/workspace/repo` contains python-titlecase 2.4.1, a small Python library. Its function
`titlecase(text)`, in `titlecase/__init__.py`, turns a line of text into a title: most words are
capitalised, small words such as "of" and "the" stay lower case, and acronyms, names, web
addresses and similar special words are handled by their own rules.

## What to build

Replace the Python implementation with a Go program in `/workspace/repo`.

- `/workspace/repo` must be the root of a Go module whose root package is `package main`.
  Running `go build -o /tmp/titlecase .` in `/workspace/repo` must produce the program.
- The program reads UTF-8 text from standard input. Every input line ends with `\n`.
- For each input line, in order, it writes the titlecased line followed by `\n` to standard
  output. The output has exactly one line per input line.
- The program takes no command-line arguments.

## Hard rules

- Use the Go standard library only: `go.mod` has no `require` or `replace` line, and there is no
  cgo. The program must build with the Go 1.23 toolchain in this image with no network access
  (`GOTOOLCHAIN=local`, `GOPROXY=off`, `GOFLAGS=-mod=mod`, `CGO_ENABLED=0`).
- `go build ./...` must pass in `/workspace/repo`.
- The program must do the conversion itself. It reads only standard input; it must not read
  other files, run any other program (for example a Python interpreter) or use the network.
  It is run as an unprivileged user.
- When you finish, no `.py` file may be left anywhere under `/workspace/repo`.

## Behaviour

For every input line, the output line must equal, byte for byte, what the original
`titlecase(line)` returns when called with its default arguments and with the optional `regex`
package installed (`titlecase.REGEX_AVAILABLE` is `True`). Python 3 with `regex` is installed in
this image, so you can run the original to see what it returns.

Input lines are valid UTF-8 and contain no `\r` or other line-break character. They are mostly
English text made of ASCII letters, digits and punctuation, and may also contain accented Latin
letters (for example `ñ`, `é`, `æ`), typographic quotes and dashes, other non-ASCII punctuation
and symbols (for example `¿`, `≤`), and whitespace characters
other than the plain space (for example tab, thin space, no-break space). An input line may
start or end with whitespace.

## Not checked

Speed, memory use, the wording of error messages, and behaviour on input that is not valid
UTF-8.

## How it is graded

Hidden automatic tests give a score from 0 to 1 with partial credit: one part for the build,
one part for the removal of the Python files (counted only if the build passes), and four parts
for the share of hidden titles whose output line matches the original exactly.
