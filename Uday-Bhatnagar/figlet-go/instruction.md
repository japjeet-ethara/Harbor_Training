# Port pyfiglet to Go

The repository at `/workspace/repo` contains the MIT-licensed pyfiglet implementation at commit `255827efbc09d662875dad50fa0edc1e1263bf45`. It renders text with FIGlet fonts, including font-controlled kerning and smushing, wrapping, direction, alignment and output transformations.

Build a Go command-line program in `/workspace/repo`. Running `go build -o /tmp/figlet .` there must create the executable. Match the original pyfiglet command's stdout byte for byte, including spaces and final newlines.

Accept `-f FONT`, `-w COLS`, `-j auto|left|center|right`, `-D auto|left-to-right|right-to-left`, `-r`, `-F`, `-s`, and `-n`, followed by one or more text arguments joined with spaces. Defaults are standard font, width 80, automatic direction and automatic justification. Width controls both wrapping and justification. Automatic direction follows the font; automatic justification follows the resolved direction. Reverse mirrors the rendered art; flip turns it upside down. Strip and normalize follow the original command's precedence and newline behavior.

Keep the standard `.flf` font files inside the repository; they may move or be embedded. The built program must work from any working directory. Use only the Go standard library. Remove every `.py` file anywhere in the repository. `go build ./...` must pass.

Speed, memory, error-message wording, and options `-c`, `-L`, `-l`, and `-i` are not checked. Hidden automatic cases award partial credit for building, removing Python source in a working port, and exact rendering behavior.
