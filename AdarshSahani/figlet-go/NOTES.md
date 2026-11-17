# PyFiglet notes

## Licence

The project uses the MIT License (also called the MIT licence).

- Repository: https://github.com/pwaller/pyfiglet
- Commit SHA: 255827efbc09d662875dad50fa0edc1e1263bf45
- Commit Date: 2026-08-02T22:51:18+01:00

## Running from a fresh clone

`python -m pyfiglet hello` needs a font resource, but a fresh checkout does not include the populated `pyfiglet/fonts/` package. The font files are held separately in `pyfiglet/fonts-standard/` (and `pyfiglet/fonts-contrib/`); the module looks for packaged fonts under `pyfiglet.fonts`. `setup.py` copies the standard fonts when it is run for a build, but simply invoking the module does not run setup.

Run `make minimal`: its steps clean and create `pyfiglet/fonts/`, copy `pyfiglet/fonts-standard/*` into it, and run `python3 -m build`. The `full` target also copies the standard fonts, plus contributed fonts, before building.

## Kerning and smushing

The examples below describe the two touching edge cells of neighboring FIGcharacters. `H` denotes the font's hardblank character. The rules apply when the font's layout flags enable them; the resulting hardblank is displayed as a space in final output.

| Rule | Tiny edge example | Result | Effect |
|---|---|---|---|
| Equal character | `A + A` | `A` | Identical non-hardblank characters merge into one. |
| Underscore (lowline) | `_ + |` | `|` | `_` merges with a character in the hierarchy set `| / \\ [ ] { } ( ) < >`; the other character wins. |
| Hierarchy | `| + /` | `/` | At each hierarchy level, the higher character wins. The levels are `|`, `/ \\`, `[ ]`, `{ }`, `( )`, then `< >`. For example, `] + {` gives `}`. |
| Opposite pairs | `[ + ]` | `|` | Matching pairs `[]`, `{}`, and `()` collapse to `|`. |
| Big X | `> + <` | `X` | `> <` becomes `X`; `/ + \\` becomes `|`, and `\\ + /` becomes `Y`. |
| Hardblank | `H + H` | `H` | Two hardblanks merge into one (then the renderer displays it as a space). A hardblank does not smush with an ordinary character. |
| Kerning | `A ` + ` B` | `A B` | Neighboring characters overlap by one or more blank edge columns, but occupied cells never merge. This is spacing overlap, without character smushing. |

Smushing is an overlap operation: for example, equal-character smushing makes the two touching `A` cells occupy one output cell. Kerning can overlap blank cells only. The builder also has universal smushing for layout mode 0: touching ordinary characters overlap and the later text character wins; hardblanks are preserved in preference to ordinary characters.

## Command-line options

| Option | What it does |
|---|---|
| `-f FONT` | Selects the FIGlet font. Defaults to `standard`. |
| `-w COLS` | Sets the output/terminal width in columns (default 80); used for wrapping and justification. |
| `-j SIDE` | Sets justification to `auto`, `left`, `center`, or `right`. `auto` follows the print direction. |
| `-D DIRECTION` | Sets text direction to `auto`, `left-to-right`, or `right-to-left`. `auto` uses the font's print direction when available. |
| `-r` | Reverses each rendered line horizontally, producing a mirror image. |
| `-F` | Flips the rendered output vertically (with character shapes flipped as defined by the renderer). |
| `-s` | Strips empty leading and trailing lines from the rendered output. |
| `-n` | Normalizes surrounding lines: ensures one empty line before and after the rendered text. |
