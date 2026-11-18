# Port pyfiglet to Go

## The repository

`/workspace/repo` contains https://github.com/pwaller/pyfiglet at commit
`255827efbc09d662875dad50fa0edc1e1263bf45` (MIT licence). pyfiglet is a Python
implementation of FIGlet: it draws text in large letters built from ordinary
characters, using `.flf` font files. When two large letters meet, it squeezes
them together using the font's smushing rules (equal characters, underscore,
hierarchy, opposite pairs, big X, hardblank, universal overlapping, kerning).
It also wraps long text, justifies it, can print right-to-left, mirror it and
flip it. All the logic is in `pyfiglet/__init__.py`. The fonts are in
`pyfiglet/fonts/` (the same files as `pyfiglet/fonts-standard/`). There is no
Python in this environment.

## What to build

A Go program in `/workspace/repo`. Running `go build -o /tmp/figlet .` in
`/workspace/repo` must produce a command-line program that accepts the same
options as `python -m pyfiglet`, followed by the text:

| Option | Values |
|---|---|
| `-f FONT` | the name of a font in `pyfiglet/fonts/`, without `.flf` (default `standard`) |
| `-w COLS` | a whole number (default `80`) |
| `-j SIDE` | `auto`, `left`, `center`, `right` (default `auto`) |
| `-D DIRECTION` | `auto`, `left-to-right`, `right-to-left` (default `auto`) |
| `-r` | mirror the output |
| `-F` | flip the output upside down |
| `-s` | strip surrounding empty lines |
| `-n` | normalize surrounding empty lines |

Each option is a separate argument (`-f slant`, not `-fslant`). Options come
before the text. The text is every remaining argument joined with single spaces,
exactly as pyfiglet does. `-w` is the width used for both wrapping and
justification: `-j center -w 40` centres within 40 columns.

The program writes to standard output **exactly the same bytes** as
`python -m pyfiglet` with the same arguments, including every space and the
final newline. Only inputs where pyfiglet finishes successfully are checked.

## Fonts

You may move the `.flf` files or embed them in the binary, but they must stay
inside `/workspace/repo`. The built program must work when it is run from any
working directory.

## Hard rules

- Go standard library only: `go.mod` must have no `require` lines. Go 1.23 is
  installed and module downloads are disabled.
- `go build -o /tmp/figlet .` must succeed in `/workspace/repo`.
- When you are done, no `.py` files may be left anywhere under `/workspace/repo`.

## Not checked

Speed, memory use, code style, error messages and exit codes, and the options
`-c`, `-L`, `-l` and `-i`.

## Grading

Hidden automatic cases, with partial credit. They check that the program
builds, that no `.py` files are left, and how many cases produce exactly the
right output.
