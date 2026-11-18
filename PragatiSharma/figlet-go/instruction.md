The repository contains pyfiglet, a Python program that turns text into large letters using FIGlet fonts. Port that rendering behavior to Go. Read the Python sources to see how fonts are loaded and how letters are spaced, smushed, wrapped, aligned, reversed, and flipped. When you are finished, the repository must contain no `.py` files.

From `/workspace/repo`, `go build ./...` must succeed, and `go build -o /tmp/figlet .` must produce the executable. Use only the Go standard library.

The executable takes the options below, then the input text. Extra text arguments are joined with spaces, as in pyfiglet. Standard output must match the original program byte for byte, including spaces, blank lines, and trailing newlines, even when options are combined. The original program writes the rendered text and then one more newline.

- `-f FONT` selects the font. The default is `standard`.
- `-w COLS` sets the width used for wrapping and alignment. The default is 80. A single rendered character wider than this width stops the program.
- `-j auto|left|center|right` sets alignment inside that width. The default is `auto`: left-to-right text is aligned left, and right-to-left text is aligned right. `center` and `right` pad each row with spaces.
- `-D auto|left-to-right|right-to-left` sets the text direction. The default is `auto`, which follows the font. A stored direction of 1 means right to left; any other stored direction means left to right. Right-to-left swaps the two sides before smushing.
- `-r` prints a mirror image. Each row is reversed, and characters that have a mirror form are swapped, such as `/` with `\` and `(` with `)`.
- `-F` turns the picture upside down. The rows run from bottom to top, and characters that have an up-down pair are swapped, such as `^` with `v` and `M` with `W`.
- `-s` skips leading blank or whitespace-only rows, preserves internal rows, and strips all trailing whitespace, including spaces at the end of the last visible row.
- `-n` adds one newline before and one after that same trimmed result. The CLI then writes its usual final newline, as already stated above the options.

Apply `-r` first, then `-F`. If both `-s` and `-n` are set, use `-s`.

Keep the `.flf` font files in the repository. You may move them within it. The executable must find its fonts when it is started from any working directory.

Speed, memory use, the wording of error messages, and the options `-c`, `-L`, `-l`, and `-i` are outside the grading scope.

Grading is automatic, and partial credit is available.
