Source URL: https://github.com/pwaller/pyfiglet
Commit SHA: 255827efbc09d662875dad50fa0edc1e1263bf45
Commit date: 2026-08-02T22:51:18+01:00

## Licence

The project uses the MIT License. `LICENSE` says anyone may use, copy, change, and share the software, as long as the copyright notice and the permission notice stay with the copies. The software is given as-is, with no warranty. `setup.py` also records the licence as MIT.

## Why fonts need a setup step

After a clone, the font files are not in the folder the program reads. They are stored in two source folders:

- `pyfiglet/fonts-standard` holds the fonts that are safe to ship in strict distributions.
- `pyfiglet/fonts-contrib` holds the extra contributed fonts.

The running package looks for fonts in `pyfiglet/fonts` (the `pyfiglet.fonts` package). That folder is not part of the clone. The Makefile builds it.

The `clean` step deletes `pyfiglet/fonts/` and creates an empty `pyfiglet/fonts/` again. The copy step is `minimal` or `full`, and both start by running `clean`:

- `make minimal` copies everything from `pyfiglet/fonts-standard` into `pyfiglet/fonts`, then builds the package.
- `make full` copies `pyfiglet/fonts-standard` and then `pyfiglet/fonts-contrib` into `pyfiglet/fonts`, then builds the package.

`setup.py` does a smaller version of the same job. If `pyfiglet/fonts` is missing when you install, it copies `pyfiglet/fonts-standard` into `pyfiglet/fonts`. It does not copy the contributed fonts. Use `make full` when you want those as well.

## The six smushing rules

Smushing is how two big letters share one column where they meet. `FigletBuilder.smushChars` looks at the character on the left edge and the character on the right edge and, if a rule allows it, replaces the pair with one character. A font turns each rule on with a bit in its layout value. A normal space is not smushed by these rules: a space next to any character simply disappears, so the other character remains. That is how letters slide into empty space.

Kerning is separate and is described after the six rules.

1. **Equal character** (value 1). If both sides are the same character, they become that one character. This rule does not apply to the font's hardblank. Example: left `A`, right `A`, result `A`.

2. **Underscore** (value 2). An underscore is replaced by any of `|`, `/`, `\`, `[`, `]`, `{`, `}`, `(`, `)`, `<`, or `>`. Example: left `_`, right `|`, result `|`.

3. **Hierarchy** (value 4). The characters are ranked in six classes, from earliest to latest: `|`, then `/\`, then `[]`, then `{}`, then `()`, then `<>`. When the two sides are in different classes, the character from the later class wins. Example: left `|`, right `/`, result `/`.

4. **Opposite pair** (value 8). A matching pair of brackets, braces, or parentheses becomes a vertical bar. The pair can face either way. Example: left `[`, right `]`, result `|`. The same thing happens for `{` and `}`, and for `(` and `)`.

5. **Big X** (value 16). Three pairs have special results. A slash followed by a backslash becomes a bar. A backslash followed by a slash becomes `Y`. A greater-than followed by a less-than becomes `X`. The opposite angle pair, `<` then `>`, is left alone. Example: left `>`, right `<`, result `X`. The other two cases are left `/` with right `\` giving `|`, and left `\` with right `/` giving `Y`.

6. **Hardblank** (value 32). The hardblank is the special blank character named in the font header. In many fonts that character is `$`. Two hardblanks become one hardblank. A hardblank does not merge with a normal drawn character. Example: left `$`, right `$`, result `$`.

If smushing is turned on but none of these six rules is selected, the code uses universal overlapping instead: the two characters still share one column, a visible character beats a hardblank, and the character that comes later in the text wins.

## Kerning

Kerning (value 64) only moves letters closer together until they touch. It does not merge the two characters that meet. In `smushChars`, if the font's smush bit (value 128) is off, the method stops and returns nothing, so the touching characters stay as two characters. `smushAmount` still lets the letters slide across blank columns, because a space is dropped when it meets another character. If neither the kerning bit nor the smush bit is set, the letters keep their full designed width and are not moved together at all.

## Command-line options

These options are defined in `main`.

- **-f** (`--font`) chooses the font. The default is `standard`.
- **-w** (`--width`) sets how many columns wide the output may be. The default is 80. The renderer uses this width when it wraps a line and when it pads a line for justification. If a single rendered character is wider than the selected width, pyfiglet raises `CharNotPrinted("Width is not enough to print this character")` and stops.
- **-j** (`--justify`) sets horizontal alignment: `auto`, `left`, `center`, or `right`. The default is `auto`. With `auto`, left-to-right text is left-aligned and right-to-left text is right-aligned. `center` and `right` pad each row with spaces so the art sits in the middle or at the right of the width from `-w`.
- **-D** (`--direction`) sets the writing direction: `auto`, `left-to-right`, or `right-to-left`. The default is `auto`, which follows the font. A font direction of 1 means right-to-left. Any other stored direction means left-to-right. Right-to-left swaps the two sides before the smushing rules run.
- **-r** (`--reverse`) prints a mirror image. Each row is reversed, and characters that have a mirror form are swapped, such as `/` with `\` and `(` with `)`.
- **-F** (`--flip`) turns the picture upside down. The rows are reversed from bottom to top, and characters that have an up-down pair are swapped, such as `^` with `v` and `M` with `W`.
- **-s** (`--strip-surrounding-newlines`) removes blank lines from the start and the end of the output. Blank lines in the middle of a character are kept.
- **-n** (`--normalize-surrounding-newlines`) makes the output start and end with exactly one empty line. If both `-s` and `-n` are given, `-s` is the one that is used.

## Rare cases

If a single rendered character is wider than the width selected with `-w`, pyfiglet raises `CharNotPrinted("Width is not enough to print this character")` and stops.

## Manually verified

- The slant font rendered "hello" successfully.
- Equal-character rule: A + A produced A.
- Opposite-pair rule: [ + ] produced |.
