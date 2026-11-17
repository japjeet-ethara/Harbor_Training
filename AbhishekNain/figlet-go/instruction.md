# Instructions

## 1. Repository

`/workspace/repo` contains `pyfiglet`, a Python implementation of FIGlet that renders text as character art using font files, fitting, smushing, wrapping, direction, and justification.

## 2. Required program

Implement a Go command-line replacement in `/workspace/repo`.
Running:
```bash
go build -o /tmp/figlet .
```
from `/workspace/repo` must produce the executable.

Support these options, followed by text:
- `-f FONT`
- `-w COLS`
- `-j auto|left|center|right`
- `-D auto|left-to-right|right-to-left`
- `-r`
- `-F`
- `-s`
- `-n`

Match the pinned pyfiglet CLI output byte for byte, including spaces, blank rows, trailing whitespace, and newlines.
Multiple positional text arguments are joined with a single space.

### Defaults
- Font: `standard`
- Width: `80`
- Justification: `auto`
- Direction: `auto`
- `-r`, `-F`, `-s`, `-n`: disabled

### Clarifications
- Justification uses the selected `-w` width, not always 80.
- Auto direction follows the font's print direction.
- Auto justification follows the resolved direction.
- `-s` takes precedence over `-n` when both are present.

## 3. Fonts and execution

Use the supplied standard fonts.
Font files may move but must remain inside the repository.
The built executable must find its fonts and work when launched from any working directory.

## 4. Constraints

- Use Go standard library only.
- Delete every `.py` file anywhere under `/workspace/repo`.
- Both `go build -o /tmp/figlet .` and `go build ./...` must pass.

## 5. Outside scope

Speed, memory usage, error-message wording, and options `-c`, `-L`, `-l`, `-i` are outside scope.

## 6. Grading

Hidden automatic evaluation awards partial credit for successful build, removal of Python source tied to functioning behavior, and exact rendering behavior.
