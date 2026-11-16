# Port pyfiglet to Go

## 1. Repository Overview
This repository contains a snapshot of `pyfiglet` (MIT License), a Python implementation of FIGlet that renders input text into large ASCII banners using `.flf` font definitions. It parses FIGlet font headers and glyph layouts, applies horizontal kerning and six horizontal smushing rules (equal character, underscore, hierarchy, opposite pair, big X, and hardblank), handles line wrapping, justification, print direction, horizontal mirroring, and vertical flipping.

## 2. What to Build
Implement a Go command-line port of `pyfiglet`'s FIGlet renderer inside `/workspace/repo`. Running `go build -o /tmp/figlet .` inside `/workspace/repo` must produce a binary `/tmp/figlet` that accepts the following options followed by the input text (joined with spaces if multiple positional arguments are given, or empty if none):

- `-f FONT`: Font name to load (default: `standard`).
- `-w COLS`: Maximum output width in columns for wrapping and alignment within those `COLS` columns (default: `80`).
- `-j auto|left|center|right`: Horizontal justification within the configured `-w` width (`auto` uses `left` for left-to-right direction and `right` for right-to-left direction; default: `auto`).
- `-D auto|left-to-right|right-to-left`: Print direction (`auto` uses the font header's `printDirection`; default: `auto`).
- `-r`: Reverse the rendered output horizontally (mirrors each line and swaps directional characters such as `/`, `\`, `(`, `)`, `[`, `]`, `{`, `}`, `<`, `>`).
- `-F`: Flip the rendered output vertically (reverses row order and maps characters vertically).
- `-s`: Strip surrounding newlines from the rendered output.
- `-n`: Normalize surrounding newlines in the rendered output.

For every supported option combination and input text, `/tmp/figlet` must produce the exact same stdout as `pyfiglet`, byte for byte.

## 3. Fonts
The `.flf` font files (currently in `pyfiglet/fonts/`) may be moved to another directory or embedded, but they must remain inside `/workspace/repo`. The compiled `/tmp/figlet` binary must locate its fonts and work properly regardless of the caller's current working directory.

## 4. Hard Rules
- Use the Go standard library only (no external third-party modules).
- Delete all `.py` files so that no `.py` file exists anywhere under `/workspace/repo`.
- `go build ./...` in `/workspace/repo` must succeed cleanly.

## 5. Not Checked
- Execution speed and memory usage.
- Error messages or exit codes on invalid flags or missing fonts.
- Unsupported CLI flags: `-c`, `-L`, `-l`, and `-i`.

## 6. Grading
Your submission is evaluated automatically against a suite of hidden test cases covering all supported options, fonts, widths, directions, justifications, and character smushing combinations, awarding a partial score based on exact byte-for-byte output matches along with build and repository cleanliness checks.
