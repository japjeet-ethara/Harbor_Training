# Build a Go FIGlet renderer

This repository contains the source and standard fonts for pyfiglet, a Python implementation of FIGlet. FIGlet renders text as large character art and combines glyphs using its font layout rules.

Build a Go command-line program in `/workspace/repo`. Running `go build -o /tmp/figlet .` in that directory must produce a program that accepts `-f FONT`, `-w COLS`, `-j auto|left|center|right`, `-D auto|left-to-right|right-to-left`, `-r`, `-F`, `-s`, `-n`, followed by text. Its stdout must match pyfiglet byte for byte for those options.

The `.flf` font files may move but must remain in the repository, and the program must work from any current directory. Use only the Go standard library. No `.py` files may remain anywhere in the repository. `go build ./...` must pass.

Speed, memory use, error messages, and the `-c`, `-L`, `-l`, and `-i` options are not graded. Grading uses hidden automatic cases and awards partial credit.
