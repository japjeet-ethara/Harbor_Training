# FIGlet Go Port

## 1. Repository Overview
This repository contains a checkout of `pyfiglet`, a Python implementation of FIGlet (a program that renders short text into large ASCII art banners using specialized FIGlet fonts). The repository includes font definitions located in `pyfiglet/fonts` and Python source files implementing font parsing, smushing, kerning, layout formatting, and CLI option handling.

## 2. What to Build
You must build a Go program in `/workspace/repo`. Running `go build -o /tmp/figlet .` in `/workspace/repo` must produce a command-line executable at `/tmp/figlet`.

The executable must accept the following command-line options identical to pyfiglet:
- `-f FONT`: Name of the font to use (default: `standard`).
- `-w COLS`: Terminal width in columns for line wrapping and justification (default: `80`).
- `-j SIDE`: Text justification: `auto`, `left`, `center`, or `right`. (`auto` follows print direction: `left` for left-to-right, `right` for right-to-left).
- `-D DIRECTION`: Text rendering direction: `auto`, `left-to-right`, or `right-to-left`. (`auto` follows the font's print direction).
- `-r`: Mirror output horizontally.
- `-F`: Flip output vertically.
- `-s`: Strip surrounding empty leading and trailing lines.
- `-n`: Normalize surrounding newlines to exactly one newline before and after rendered output (overridden by `-s` if both are specified).

Any remaining command-line arguments are joined with a single space to form the input text string. The program must print the rendered ASCII banner to standard output, matching pyfiglet's output byte for byte for all supported options and inputs.

## 3. Fonts
The `.flf` font files may be relocated within the repository or embedded into the Go binary (e.g. using Go `embed`), but all necessary font definitions must remain inside the repository. The compiled program must function correctly regardless of the current working directory from which it is executed.

## 4. Hard Rules
- Use only the Go standard library (no third-party dependencies).
- Remove all `.py` files from the repository upon completion (no `.py` files anywhere in `/workspace/repo`).
- `go build ./...` must succeed without errors.

## 5. Not Checked
- Execution speed and memory efficiency.
- Exact error messages on invalid input.
- Unsupported options: `-c`, `-L`, `-l`, `-i`.

## 6. Grading
Submissions are evaluated against hidden automated test cases measuring build success, repository hygiene (no `.py` files), and behavioral exactness. Partial scores are awarded based on the proportion of cases matching expected output.
