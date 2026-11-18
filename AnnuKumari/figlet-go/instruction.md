# Instructions

## 1. What the Repository Is

The repository is pyfiglet (cloned from https://github.com/pwaller/pyfiglet at commit `255827efbc09d662875dad50fa0edc1e1263bf45`, licensed under the MIT License), a pure Python port of FIGlet that renders ASCII text into ASCII art banners using FIGlet font (`.flf`) files. It contains standard font definitions (located in `pyfiglet/fonts-standard` and `pyfiglet/fonts`) along with the rendering engine supporting FIGlet font parsing, horizontal smushing rules, kerning, line wrapping, and command-line layout formatting.

## 2. What to Build

Build a Go program in `/workspace/repo`. Running `go build -o /tmp/figlet .` in `/workspace/repo` must produce a command-line program that accepts the same options as pyfiglet:
- `-f FONT`: font name to render with (default: `standard`).
- `-w COLS`: column width used for wrapping and justification (default: `80`).
- `-j auto|left|center|right`: text justification (`auto`, `left`, `center`, `right`).
- `-D auto|left-to-right|right-to-left`: text formatting direction (`auto`, `left-to-right`, `right-to-left`).
- `-r`: reverse (mirror each output row).
- `-F`: flip (turn the figure upside down).
- `-s`: strip surrounding newlines (drop empty lines before the figure starts and after it ends).
- `-n`: normalize surrounding newlines (same trimming as `-s`, then one empty line before the figure and one after it; if both `-s` and `-n` are set, `-s` is applied and `-n` is not).

followed by the text. It prints the same output as pyfiglet, byte for byte.

## 3. Fonts

The `.flf` files may move, but must stay in the repository. The program must work from any working directory.

## 4. Hard Rules

- Go standard library only.
- No `.py` files anywhere in the repository.
- `go build ./...` must pass.

## 5. Not Checked

- Speed
- Memory
- Error messages
- The options `-c`, `-L`, `-l`, `-i`

## 6. Grading

Grading is based on hidden automatic cases, with partial score awarded.
