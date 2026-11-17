# Task

## 1. Repository

PyFiglet is the `pwaller/pyfiglet` repository, an MIT-licensed Python implementation of FIGlet. The task is based on commit `255827efbc09d662875dad50fa0edc1e1263bf45`; its notes describe the FIGlet font resources and rendering behavior, including kerning, smushing, direction, and justification.

## 2. What to build

Build a Go program in `/workspace/repo`. Running `go build -o /tmp/figlet .` from `/workspace/repo` must produce a command-line program that accepts `-f FONT`, `-w COLS`, `-j auto|left|center|right`, `-D auto|left-to-right|right-to-left`, `-r`, `-F`, `-s`, and `-n`, followed by the text to render. For supported invocations, its output must match pyfiglet byte for byte.

## 3. Fonts

The `.flf` font files may be moved within the repository, but they must remain in the repository. The program must locate and use them when launched from any working directory.

## 4. Hard rules

- Use only the Go standard library.
- Do not leave any `.py` files anywhere in the repository.
- `go build ./...` must pass.

## 5. Not checked

Speed, memory use, and error messages are not checked. The options `-c`, `-L`, `-l`, and `-i` are not checked.

## 6. Grading

Grading uses hidden automatic cases and awards partial credit.
