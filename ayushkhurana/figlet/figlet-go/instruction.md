# Port pyfiglet to Go

## The repository

`/workspace/repo` holds **pyfiglet 1.0.4**, a Python implementation of FIGlet: it draws text in giant letters made of ASCII characters, read from `.flf` font files. When two letters stand next to each other it squeezes them together ("smushing" and kerning, depending on the font), wraps long text, justifies it, and can mirror or flip the picture. The code is in `pyfiglet/__init__.py` (`FigletFont`, `FigletBuilder`, `FigletString` and `main()`); the fonts are in `pyfiglet/fonts/` (a copy of `pyfiglet/fonts-standard/`). The project is MIT licensed. Python is **not** installed in this environment, so you cannot run the original; you have to read it.

## What to build

A Go program in the root package of `/workspace/repo`. The command

```
cd /workspace/repo && go build -o /tmp/figlet .
```

must produce a command-line program that behaves like `python -m pyfiglet` (that is, `main()` in `pyfiglet/__init__.py`) for these options:

```
/tmp/figlet [-f FONT] [-w COLS] [-j auto|left|center|right] [-D auto|left-to-right|right-to-left] [-r] [-F] [-s] [-n] TEXT...
```

- The options come first, in any order. Every option that takes a value gets it as a separate argument (`-w 40`, not `-w40`). Everything after the options is the text: the words are joined with one single space, exactly as the original does. No text word starts with `-`.
- The output on stdout must be identical to the original's, byte for byte, including every space and the final newline, and the exit status must be 0.
- The defaults are the original's: font `standard`, width 80, `-j auto`, `-D auto`.
- `-w` is the width used both for wrapping and for `-j center` / `-j right`: with `-w 40 -j center` the picture is centred in 40 columns, not 80.
- The text may contain spaces, punctuation, digits, Latin-1 letters, characters the font does not have, and newline characters inside a text argument. Whatever the original does with them, the program must do the same.
- When `-s` and `-n` are both given, the program must do what the original does.

## Fonts

The eight fonts used in grading are `standard`, `slant`, `small`, `big`, `mini`, `banner`, `shadow` and `script`; their files are in `pyfiglet/fonts-standard/` and `pyfiglet/fonts/`. The `.flf` files may be moved, but they must stay inside the repository.

The program is built to `/tmp/figlet` and run from another working directory, as an unprivileged user with a minimal environment, while the repository stays at `/workspace/repo`. It must find its fonts in that situation (embedding them with `go:embed` is one way).

## Hard rules

- Go standard library only: no third-party packages, not even local copies of them. The Go toolchain is fixed (Go 1.23) and nothing can be downloaded during grading.
- Do not import `os/exec`, `syscall`, `unsafe`, `plugin` or `net`, and do not import any package that depends on `os/exec`, `net` or `plugin` (for example `net/http`). No cgo, no assembly or C files, no `//go:linkname`, no `os.StartProcess`.
- When you are done there must be no `.py` file anywhere in `/workspace/repo`.
- `go build ./...` must succeed in `/workspace/repo`, and so must the build command above.

## Not checked

Speed, memory use, error messages, exit codes for failing inputs, invalid arguments, the options `-c`, `-L`, `-l`, `-i`, `-h`, `--version`, long option names, combined short flags such as `-rF`, and fonts other than the eight above. Inputs for which the original itself fails or never finishes (for example a width too small for a letter) are not tested.

## How it is graded

Your program is built and then run on many hidden cases (an argument list, and the exact stdout expected). The score is a weighted mean of three parts: the program builds (weight 1); the hard rules hold and the program gets at least one case right (weight 1); and the share of cases whose output is exactly right, each run limited to 5 seconds (weight 4). A program that breaks a hard rule earns nothing for the third part.
