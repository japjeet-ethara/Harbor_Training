# pyfiglet notes

## Repository information

Repository: https://github.com/pwaller/pyfiglet

Commit SHA: 255827efbc09d662875dad50fa0edc1e1263bf45

Commit Date: 2026-08-02T22:51:18+01:00

License: MIT

These notes are based on `pyfiglet/__init__.py`, `Makefile`, `setup.py`, and
`LICENSE`.

## 1. License

pyfiglet uses the **MIT License (MIT)**. This is stated at the top of
`LICENSE`, in the `__copyright__` text in `pyfiglet/__init__.py`, and as
`license='MIT'` and the MIT classifier in `setup.py`.

In simple terms, the MIT License allows people to use, copy, modify, publish,
and sell the software, provided that the copyright and permission notice stay
with copies or substantial portions. The software is provided without a
warranty.

## 2. Why `python -m pyfiglet hello` fails immediately after cloning

The repository contains the font sources in `pyfiglet/fonts-standard/` and
`pyfiglet/fonts-contrib/`, but a fresh checkout does not contain the runtime
directory `pyfiglet/fonts/`.

`FigletFont.preloadFont()` looks for the selected font through the package
resource `pyfiglet.fonts` and then through system directories. The default
font is `standard`. Therefore, before the fonts have been copied into the
runtime package directory, loading `standard.flf` fails and raises
`FontNotFound`. The command-line code catches that exception and prints:

```text
pyfiglet error: requested font 'standard' not found.
```

`setup.py` creates `pyfiglet/fonts/` only when packaging/setup is run: if the
directory is absent, it copies `pyfiglet/fonts-standard` there. A plain clone
does not run `setup.py`, so it can fail before that setup step occurs.

## 3. Makefile step that fixes it

The `minimal` target fixes the missing-font problem:

```make
minimal:    clean
	cp pyfiglet/fonts-standard/* pyfiglet/fonts
	python3 -m build
```

`clean` removes any old `pyfiglet/fonts/` directory and recreates it. The next
command copies the standard font files into it, and then the package is built.
The `full` target also fixes the problem because it performs the same standard
font copy and additionally copies the contributed fonts:

```make
full:    clean
	cp pyfiglet/fonts-standard/* pyfiglet/fonts
	cp pyfiglet/fonts-contrib/* pyfiglet/fonts
	python3 -m build
```

For the normal minimal package, the relevant fix is `make minimal`.

## 4. Smushing rules and kerning

The `FigletBuilder` defines six smushing rules. A smush happens when the
right edge of one rendered character meets the left edge of the next one.
`smushChars(left, right)` returns the character that should occupy the
overlapping column; returning `None` means that pair should not be overlapped.
The examples below show only the two touching edge characters, not complete
font glyphs. Each example assumes the relevant smush-mode bit is enabled and
that both glyphs have width at least two, as required by `smushChars()`.

The implementation checks ordinary spaces first, and hardblanks are treated
separately. A font's `smushMode` bits decide which rules are enabled.

### Rule 1: Equal-character smushing (`SM_EQUAL`)

Two equal, non-hardblank characters collapse to one copy:

```text
left + right:  | + |  ->  |
```

The source explicitly excludes hardblanks from this rule; hardblank handling
uses the separate rule below.

### Rule 2: Underscore smushing (`SM_LOWLINE`)

An underscore can merge with one of the hierarchy characters
`| / \ [ ] { } ( ) < >`. The hierarchy character wins:

```text
_ + |  ->  |
```

The rule is symmetric in the source, so `| + _` also produces `|`.

### Rule 3: Hierarchy smushing (`SM_HIERARCHY`)

Characters are ordered from weaker to stronger:

```text
|,  /\,  [],  {},  (),  <>
```

When one character from a lower group meets one from a higher group, the
higher-group character wins. For example:

```text
| + /  ->  /
```

The reverse order also leaves the higher-group character:

```text
/ + |  ->  /
```

The source applies this same ordering to the other groups, such as `[]` versus
`{}` and `{}` versus `()`.

### Rule 4: Opposite-pair smushing (`SM_PAIR`)

Matching brackets from these pairs become a vertical bar:

```text
[ + ]  ->  |
{ + }  ->  |
( + )  ->  |
```

The source tests both orders, so `] + [` also becomes `|`, for example.

### Rule 5: Big-X smushing (`SM_BIGX`)

The source has three explicit cases:

```text
/ + \  ->  |
\ + /  ->  Y
> + <  ->  X
```

The first two results are exactly what this Python implementation returns; the
reverse slash case is not `X` despite the nearby constant comment describing
the rule as “big X”.

### Rule 6: Hardblank smushing (`SM_HARDBLANK`)

A hardblank is the special placeholder character declared by a `.flf` font.
When `SM_HARDBLANK` is enabled and both touching characters are hardblanks,
they collapse into one hardblank:

```text
hardblank + hardblank  ->  hardblank
```

A hardblank touching an ordinary visible character is not handled by this
specific rule; after the hardblank-pair check, `smushChars()` returns `None`.
After rendering, `replaceHardblanks()` changes hardblanks to ordinary spaces.

The implementation also has a separate universal-smushing mode, selected when
`SM_SMUSH` is enabled and none of the six rule bits (`SM_EQUAL` through
`SM_HARDBLANK`) are enabled. In that mode hardblanks are handled specially:
when one side is a hardblank, the other side wins, so a hardblank can overlap
an ordinary visible character instead of returning `None`.

### Kerning (`SM_KERN`)

Kerning allows characters to come closer by overlapping a column when the
edges permit it, especially when an edge contains an ordinary space. It does
not combine two visible edge characters into a new character. For example,
the conceptual edge result is:

```text
A + (space at the touching edge)  ->  A
```

In `smushAmount()`, kerning makes the builder calculate a possible overlap.
`SM_SMUSH` is the separate bit required for actual visible-character
smushing. `smushChars()` also refuses overlap when either glyph is narrower
than two columns. Thus a font can use kerning without enabling the six
visible-character replacement rules.

## 5. Command-line options

The options are registered in `main()` in `pyfiglet/__init__.py`.

| Option | Meaning |
| --- | --- |
| `-f FONT` / `--font FONT` | Select the FIGlet font. The default is `standard`. |
| `-w COLS` / `--width COLS` | Set the terminal width used for wrapping and justification. The default is `80`. It is parsed as an integer. |
| `-j SIDE` / `--justify SIDE` | Choose `auto`, `left`, `center`, or `right` justification. `auto` follows the effective print direction. |
| `-D DIRECTION` / `--direction DIRECTION` | Choose `auto`, `left-to-right`, or `right-to-left` text formatting. `auto` uses the direction stored in the font, falling back to left-to-right when the font does not specify one. |
| `-r` / `--reverse` | Mirror the rendered output horizontally. `FigletString.reverse()` reverses each row and translates the slash/backslash and other drawing characters using its reverse map. |
| `-F` / `--flip` | Flip the rendered output vertically. `FigletString.flip()` reverses the row order and translates drawing characters using its flip map. |
| `-s` / `--strip-surrounding-newlines` | Remove empty leading and trailing rendered lines. This is applied after rendering; it does not strip empty lines in the middle. |
| `-n` / `--normalize-surrounding-newlines` | Ensure exactly one empty line before and after the rendered text, using the renderer's newline normalization method. `-s` takes precedence if both are supplied because the code checks it first. |

