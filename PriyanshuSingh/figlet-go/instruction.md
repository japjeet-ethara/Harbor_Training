# Port pyfiglet to Go

## About the repository

The repository is located at `/workspace/repo`. It contains pyfiglet, a Python implementation of FIGlet, at commit `255827efbc09d662875dad50fa0edc1e1263bf45`. The project is licensed under the MIT License.

FIGlet converts regular text into large text made up of ordinary characters. It uses `.flf` font files to determine how each character should look. When two characters are placed next to each other, `FigletBuilder` can bring them closer together through a process called smushing. The font's header defines the rules used for this.

The existing Python implementation is in `pyfiglet/__init__.py`. Besides rendering text, it also supports line wrapping, justification, right-to-left output, mirroring, and upside-down text.

The font setup has already been completed. The directory `pyfiglet/fonts/` contains a copy of `pyfiglet/fonts-standard/`, so all required font files are available locally. Python is not installed in the container.

## What needs to be implemented

Replace the existing Python implementation with a Go program inside `/workspace/repo`.

The project must build successfully using:

```bash
go build -o /tmp/figlet .
```

The resulting executable, `/tmp/figlet`, should behave like `python -m pyfiglet` from the specified commit.

It must support the following command-line options:

| Option | Description |
|---|---|
| `-f FONT` | Select a font by name. For example, `slant`. The default is `standard`. |
| `-w COLS` | Set the output width used for wrapping and justification. The default is `80`. |
| `-j auto\|left\|center\|right` | Choose how the output is justified. The default is `auto`. |
| `-D auto\|left-to-right\|right-to-left` | Set the direction in which the text is displayed. The default is `auto`. |
| `-r` | Mirror the generated output. |
| `-F` | Flip the output upside down. |
| `-s` | Remove empty lines from the beginning and end of the output. |
| `-n` | Add one empty line before and after the output. |

### Command-line argument handling

Options must be accepted before, between, or after the text arguments. Their order should not matter.

In every command line that is checked, each option and its value are separate arguments. For example, `-w 40` is used, never `-w40`.

Any argument that is not an option or the value of an option should be treated as text. The text arguments must be combined into a single string, with exactly one space between consecutive arguments.

Text arguments will not start with `-`, but they may be empty, contain newline characters, or include characters that are not available in the selected font.

For every supported command line, the Go program must produce exactly the same standard output as the original Python implementation. The comparison is byte-for-byte, so even small differences matter. This includes spacing, blank lines, and the final newline.

## Font support

All fonts available in `pyfiglet/fonts/` must be supported and selectable by their font names.

The `.flf` files can either remain in their current location or be embedded into the Go executable using `go:embed`. In either case, they must remain within `/workspace/repo`.

The compiled program must be completely self-contained with respect to its font access. It should work:

- From any working directory.
- When executed by a different unprivileged user.
- When `/tmp/figlet` is the only copy of the executable.

If the program reads font files directly, those files must be readable by all users, and it must not depend on the current working directory.

## Important restrictions

The implementation must follow these requirements:

- Use only the Go standard library. No external Go dependencies are allowed.
- The build environment has no network access or Go module proxy.
- Remove every `.py` file from `/workspace/repo`. No Python files should remain anywhere in the repository.
- The command `go build ./...` must complete successfully from `/workspace/repo`.

## What will not be tested

The following features and situations are outside the scope of testing:

- Performance and memory consumption.
- Error messages and exit codes for invalid input.
- Commands that cause the original pyfiglet implementation to fail or run indefinitely.
- The options `-c`, `-L`, `-l`, and `-i`.

## Grading criteria

The implementation will be evaluated using hidden automated tests. The grading is divided into three parts:

1. **Build requirements (weight: 1):** Both required Go build commands must succeed.
2. **Basic implementation requirements (weight: 1):** No `.py` files may remain, the project must build successfully, and at least one test case must produce the correct output.
3. **Output accuracy (weight: 4):** This part scores the proportion of hidden test cases where the Go program's output matches the original Python implementation exactly.

The final score is the weighted average of the three parts, with partial credit. Each test case has a time limit of five seconds.
