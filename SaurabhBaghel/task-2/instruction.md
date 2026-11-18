# pyfiglet Go Port

## 1. Overview
This repository contains `pyfiglet`, a Python implementation of FIGlet that renders plain text into large ASCII art letters using FIGlet fonts (`.flf`). It parses FIGlet font files, handles character layout, smushing rules (equal characters, lowline, hierarchy, pair, big-X, hardblank), universal overlapping, kerning, word wrapping, alignment, and text transformations.

## 2. What to Build
Implement a pure Go replacement for `pyfiglet` in `/workspace/repo`.
Running `go build -o /tmp/figlet .` inside `/workspace/repo` must produce an executable command-line program `/tmp/figlet`.

The command-line program must accept the following command-line flags followed by positional text arguments:
- `-f FONT`: Font name to render with (e.g. `standard`, `slant`, `small`, `big`, `mini`, `banner`, `shadow`, `script`).
- `-w COLS`: Terminal width in columns (integer) used for wrapping and justification (default: 80).
- `-j SIDE`: Justification: `auto`, `left`, `center`, or `right`. When `auto`, defaults to the print direction (`left` for left-to-right, `right` for right-to-left). When `center` or `right` is specified, pad lines with spaces relative to the column width specified by `-w COLS`.
- `-D DIRECTION`: Print direction: `auto`, `left-to-right`, or `right-to-left`. When `auto`, defaults to the font's default print direction.
- `-r`: Mirror image / reverse rendered output horizontally.
- `-F`: Flip rendered output vertically upside down.
- `-s`: Strip empty leading and trailing lines from the rendered output.
- `-n`: Normalize surrounding newlines so the output has exactly one empty line before and one empty line after.

All positional arguments following flags are joined with a single space into the input text string (`" ".join(args)`).
The program must print the rendered FIGlet ASCII output to standard output, matching the original `pyfiglet` output byte for byte.

## 3. Fonts
The font files (`.flf`) in the repository may be moved or embedded (e.g. via `//go:embed`), but must remain accessible; `/tmp/figlet` must work regardless of what current working directory it is executed from.

## 4. Hard Rules
- Go standard library only. External third-party packages or Go modules are not permitted.
- No `.py` files may exist anywhere in `/workspace/repo`. All original Python files must be deleted.
- `go build ./...` must succeed without errors.

## 5. Excluded Features (Not Evaluated)
- Execution speed, memory usage, and exact error message formatting are not evaluated.
- The pyfiglet options `-c` (color), `-L` (font install), `-l` (font list), and `-i` (font info) are not evaluated and do not need to be implemented.

## 6. Grading
Submissions are evaluated automatically against a suite of test cases with partial scoring based on build success, absence of Python files, and behavioral correctness.
