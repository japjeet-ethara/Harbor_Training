# Port pyfiglet to Go

## 1. The Repository

`/workspace/repo` contains `pyfiglet` (version 1.0.4), a Python implementation of FIGlet. FIGlet takes input text and renders it into large ASCII art lettering banners using FIGlet fonts (`.flf` files). The rendered characters are shaped from character matrices that can be compressed horizontally using controlled smushing rules (equal characters, lowline/underscore, character hierarchy, bracket/brace/parenthesis pairs, big X, and hardblanks) or kerning, wrapped at specified column widths, aligned, horizontally reversed (mirrored), or vertically flipped.

## 2. What to Build

Replace the Python implementation with a Go program in `/workspace/repo`.

- `/workspace/repo` must be the root of a Go module whose root package is `package main`.
- Running `go build -o /tmp/figlet .` in `/workspace/repo` must produce an executable command-line program at `/tmp/figlet`.
- The program accepts the same command-line options as `pyfiglet`, followed by the text to render:
  - `-f FONT`: Font name to render with (default: `standard`).
  - `-w COLS`: Terminal width in columns (default: `80`). Controls the column width used for both line wrapping and text justification.
  - `-j auto|left|center|right`: Text justification across COLS columns (default: `auto`). Calculated independently for each rendered row of length L:
    - `auto`: Aligns left for left-to-right direction, right for right-to-left direction.
    - `left`: 0 leading spaces.
    - `center`: `max(0, (COLS - L) // 2)` leading spaces (uses the supplied COLS, not assuming 80 columns).
    - `right`: `max(0, COLS - L - 1)` leading spaces.
  - `-D auto|left-to-right|right-to-left`: Text formatting direction (default: `auto`). In `auto`, direction is determined by the font header (`0` for left-to-right, `1` for right-to-left).
  - `-r`: Horizontal reverse (mirror) flag. Reverses the output horizontally by reversing character order on each row and translating paired glyph sub-characters according to the FIGlet reverse character mapping.
  - `-F`: Flip flag. Inverts the output vertically by reversing line order and translating vertical glyph sub-characters according to the FIGlet flip character mapping.
  - `-s`: Strip surrounding newlines flag. Removes empty leading lines before and empty trailing lines after the rendered text.
  - `-n`: Normalize surrounding newlines flag. Strips surrounding newlines and wraps output with exactly one empty line before and one empty line after the rendered text. If `-s` is also specified, `-s` takes precedence.
- If multiple positional text arguments are provided, they are joined with single spaces.
- The output written to standard output must match the output of `pyfiglet` byte for byte.

## 3. Fonts

- The `.flf` font files may be moved to any directory within the repository (or embedded into the Go binary using `//go:embed`), but they must remain inside `/workspace/repo`.
- The compiled program must function correctly when executed from any working directory.

## 4. Hard Rules

- **Go standard library only**: `go.mod` must not require any external dependencies, and cgo must not be used (`CGO_ENABLED=0`). The program must build using the local Go 1.23 toolchain with no network access.
- **No Python files**: When finished, no `.py` file may remain anywhere under `/workspace/repo`.
- **Clean build**: `go build ./...` must pass without errors in `/workspace/repo`.

## 5. Not Checked

- Speed and memory usage.
- Exact wording of error messages or help text.
- Options not listed above (specifically `-c`, `-L`, `-l`, and `-i` are not checked).

## 6. Grading

Submissions are graded automatically against hidden cases with partial score:
- Build: successful compilation of `/tmp/figlet`.
- File cleanup: complete removal of all `.py` files under `/workspace/repo` (credited only when the build succeeds and cases match).
- Behaviour: share of hidden cases where `/tmp/figlet` produces byte-identical output to the reference implementation.
