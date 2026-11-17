# Port pyfiglet to Go

## 1. Repository Overview
The repository in `/workspace/repo` contains the reference implementation of `pyfiglet` (an MIT-licensed Python FIGlet implementation) along with its standard fonts. Your goal is to port this reference implementation into an equivalent Go command-line tool.

## 2. What to Build
Work inside `/workspace/repo`. Running the following command from `/workspace/repo` must produce the executable at `/tmp/figlet`:

```bash
go build -o /tmp/figlet .
```

The CLI must accept options followed by text (`/tmp/figlet [options] [text...]`) and support these options:
- `-f FONT`: font name (default: `standard`)
- `-w COLS`: output width in columns (default: `80`)
- `-j auto|left|center|right`: text justification (default: `auto`)
- `-D auto|left-to-right|right-to-left`: layout and printing direction (default: `auto`)
- `-r`: reverse/mirror rendered output horizontally
- `-F`: flip rendered output vertically
- `-s`: strip surrounding newlines and trailing whitespace
- `-n`: normalize surrounding newlines

### Behavioral Specifications
The CLI stdout must match the original `pyfiglet` CLI byte for byte, including spaces and newlines:
- **Defaults:** font `standard`, width `80`, justification `auto`, direction `auto`.
- **Text arguments:** Multiple text arguments are joined with single spaces.
- **Direction resolution:** When `-D` is `auto`, direction follows the font's header print direction.
- **Justification resolution:** When `-j` is `auto`, justification follows the resolved direction (`left` for left-to-right, `right` for right-to-left).
- **Explicit justification:** When explicit justification (`left`, `center`, `right`) is set, padding uses the selected `-w` width.
- **Transformations:** `-r` mirrors the rendered output text; `-F` flips the output rows vertically.
- **Newline handling:** `-s` takes precedence when both `-s` and `-n` are present.

## 3. Fonts
- Standard `.flf` font files may move but must remain inside the repository.
- The compiled program must work when invoked from any working directory. Do not require fonts to be found relative to the process's current working directory (e.g. you may embed them into the binary using Go's `embed` package).

## 4. Hard Requirements
- **Standard library only:** Use only the Go standard library.
- **No Python files:** No `.py` files anywhere under `/workspace/repo` in the finished solution.
- **Clean build:** `go build ./...` must pass.

## 5. Outside Scope
- Performance and memory use are not graded.
- Error-message wording is not graded.
- Options `-c`, `-L`, `-l`, and `-i` are not graded.

## 6. Grading
Hidden automatic evaluation awards partial credit for build success, Python-source removal, and matching behavior. Python-source-removal credit additionally requires a successful build and at least one correct behavioral result.
