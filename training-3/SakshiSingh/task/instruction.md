# Port python-titlecase to Go

## What is in this repository

`/workspace/repo` is a checkout of **python-titlecase 2.4.1** (MIT licence), a small
Python library that turns a sentence into Title Case while being clever about
small words such as `a`, `an`, `and`, `of`, `the`, `to`, `via` and `vs`.
The behaviour you must reproduce is the single public function
`titlecase(text)` in `titlecase/__init__.py`.

**Which original the answers come from:** every expected answer was produced by
python-titlecase 2.4.1 running **WITHOUT the `regex` package**, i.e. on Python's
standard-library `re` module (`titlecase.REGEX_AVAILABLE == False`). The library
behaves differently when `regex` is installed; match the `re` behaviour.

## What to build

A Go program in `/workspace/repo` that is a drop-in replacement for the Python
function:

- it reads titles from **standard input, one title per line**;
- it prints the titlecased result for each line to **standard output**;
- it prints exactly one output line per input line, in the same order;
- it prints nothing else (no prompts, banners, logs or diagnostics on stdout).

## Hard rules (all of these are checked)

1. `go build ./...` succeeds in `/workspace/repo` using Go 1.23 with **no network access**.
2. The module root is `package main`, so `go build -o /tmp/titlecase .` produces the program.
3. **Go standard library only.** `go.mod` must not require any external module.
4. At the end, **no file whose name ends in `.py` may remain anywhere under
   `/workspace/repo`** (including the `titlecase/` directory). The Python code is
   your reference while you work; it must be gone when you finish.
5. The output must match the original Python `titlecase.titlecase(line)` **byte for
   byte** for every input line: same letters, same case, same punctuation and the
   same spacing.
6. **The program must work on its own.** It is built with `CGO_ENABLED=0` and run
   as an unprivileged user inside an empty directory that contains nothing but the
   program itself: no other files, no Python, no shell, no network. It may only
   read standard input and write standard output. Calling another program or
   reading files will not work.

> Tip: deleting the `.py` files can leave `titlecase/` empty. Remove the empty
> directory (`rmdir titlecase`) before running a bare `go build ./...`: Go names
> its output after the module, and a directory with that name makes the command
> fail with `build output "titlecase" already exists and is a directory`.
> Alternatively, build with `go build -o /tmp/titlecase .`.

## Not checked

- speed or memory use;
- the wording of error messages (there should be none on valid input);
- comments, formatting or file layout beyond the rules above.

## How you are graded

Hidden automatic tests run after you stop, on 100,000 hidden titles. The score is
a weighted mean:

- **behaviour** (weight 4): the share of hidden titles whose output matches the
  original Python library exactly;
- **build** (weight 1): `go build ./...` passes **and** behaviour is at least 0.5;
- **no_python** (weight 1): no `.py` file remains, the build passes **and**
  behaviour is at least 0.5.

Partial credit is given for behaviour. A program that builds but is not a real
port earns nothing. Doing nothing scores 0.
