# Port pyfiglet to Go

## Repository

`/workspace/repo` holds pyfiglet 1.0.4 (MIT licence), a Python version of FIGlet: a command-line program that draws a short text in large letters made of ordinary characters. Its code is `/workspace/repo/pyfiglet/__init__.py`; its fonts are the `.flf` files in `/workspace/repo/pyfiglet/fonts`.

## What to build

Replace the Python program with a Go program that draws the same output. `go.mod` and the main package are in `/workspace/repo` itself: `go build -o /tmp/figlet .`, run in `/workspace/repo`, must produce the program.

The program takes these options of pyfiglet, followed by the text:

- `-f FONT`: the font, the name of a file in the fonts folder without `.flf` (default `standard`)
- `-w COLS`: the width in columns, used for wrapping and for justification (default `80`)
- `-j auto|left|center|right`: justification inside the width given by `-w` (default `auto`)
- `-D auto|left-to-right|right-to-left`: direction (default `auto`)
- `-r`: mirror the output
- `-F`: flip the output upside down
- `-s`: remove the empty lines around the output
- `-n`: one empty line before and one after the output

Each option is given at most once, as its own argument, with its value as the next argument. The options come in any order, all before the text. The text is one or more arguments, joined with single spaces; no text argument starts with `-`. The text can contain a line break, characters outside ASCII, and characters the font does not have.

For every such command line, what the program writes to standard output must equal, byte for byte, what this version of pyfiglet writes to standard output for the same arguments.

## Fonts

The font files may be moved or built into the program, but the font files the program uses must stay inside `/workspace/repo`. The program is started from other working directories and must still find its fonts.

## Hard rules

- Use the Go standard library only. The build runs offline with the Go 1.23 toolchain in the container, so a module that has to be downloaded does not build.
- `go build ./...`, run in `/workspace/repo`, must pass.
- At the end no file whose name ends in `.py` exists anywhere under `/workspace/repo`.

## Not checked

Memory use, error messages, the options `-c`, `-L`, `-l` and `-i`, command lines for which pyfiglet itself stops with an error or draws nothing, and speed, except that each run must finish within 5 seconds.

## Grading

Hidden automatic cases give a partial score from three things: whether the build passes; whether the repository is clean (no `.py` file, the fonts still inside it), which counts only when the build passes and at least one case is right; and the share of cases whose output is exactly right, which counts four times as much as each of the other two.
