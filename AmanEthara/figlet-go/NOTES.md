# pyfiglet notes

## 1. Repository and pinned commit

- Repository: https://github.com/pwaller/pyfiglet
- Pinned commit: `255827efbc09d662875dad50fa0edc1e1263bf45`
- Subject: `Return False from isValidFont for a missing font (#161)`

`origin` in this checkout points at that GitHub repository. The commit is the current `HEAD`. Under `pyfiglet/`, the commit tracks `fonts-standard/` and `fonts-contrib/`. It does not track `pyfiglet/fonts/`.

## 2. Commit date and licence

The committer date is 2026-08-02 22:51:18 +0100. The author date is 2026-08-03 03:21:18 +0530. Those are the same instant (2026-08-02 21:51:18 UTC).

The licence is the MIT License. `LICENSE` is titled “The MIT License (MIT)”. `setup.py` sets `license='MIT'` and the classifier `License :: OSI Approved :: MIT License`. The same licence text is copied into `__copyright__` in `pyfiglet/__init__.py`. Copyright line in `LICENSE`: 2007–2018, Christopher Jones, Stefano Rivera, Peter Waller, and contributors.

## 3. Why `python -m pyfiglet hello` fails after clone

`python -m pyfiglet` runs `pyfiglet/__main__.py`, which calls `main()` in `pyfiglet/__init__.py`. With no `-f`, the font is `DEFAULT_FONT`, `'standard'`. `Figlet` then constructs `FigletFont('standard')`, and `preloadFont` resolves the font with:

```python
path = importlib.resources.files('pyfiglet.fonts').joinpath(fn)
```

`fn` is `standard.tlf`, then `standard.flf`. `importlib.resources.files` imports the package `pyfiglet.fonts` before any filesystem fallback. After a clone that package does not exist: font files live in `pyfiglet/fonts-standard/` and `pyfiglet/fonts-contrib/`, and `pyfiglet/fonts/` is absent. The import raises:

```text
ModuleNotFoundError: No module named 'pyfiglet.fonts'
```

The fallback search (`./`, `/usr/local/share/pyfiglet/`, `/usr/local/share/figlet`, `/usr/share/figlet`) never runs, because the exception is raised while building the resource path. `main()` only catches `FontNotFound`, so this traceback exits the process.

`setup.py` would copy `fonts-standard` into `pyfiglet/fonts` with `shutil.copytree`, but only when `pyfiglet/fonts` is not already a directory, and only when `setup.py` itself runs. `python -m pyfiglet` does not run `setup.py`.

### Makefile step that installs the fonts

`make clean` deletes `pyfiglet/fonts/` and recreates it as an empty directory. An empty directory is importable, so the error changes to the caught `FontNotFound` path:

```text
pyfiglet error: requested font 'standard' not found.
```

`clean` does not add `standard.flf`. It also makes `setup.py` skip its `copytree`, because `pyfiglet/fonts` is now a directory. The following `python3 -m build` in the build targets therefore does not fill the directory.

The copy that installs the default font is in the `minimal` target, after `clean`:

```make
cp pyfiglet/fonts-standard/* pyfiglet/fonts
```

That copies `standard.flf` and `fonts-standard/__init__.py` (a single newline) into `pyfiglet/fonts/`. `preloadFont` can then load `standard` from the package resources. The `full` target runs that same `cp`, then also copies `pyfiglet/fonts-contrib/*` into `pyfiglet/fonts`. Either target’s standard-font copy is what makes `python -m pyfiglet hello` render. `minimal` is enough for the default font.

## 4. Smushing rules and kerning

`FigletBuilder` uses the layout bitmask from the font header (`FigletFont.smushMode`, the full-layout field when present). The flags defined on the builder are:

| Flag | Value | Role in this code |
| --- | ---: | --- |
| `SM_EQUAL` | 1 | Rule 1 |
| `SM_LOWLINE` | 2 | Rule 2 |
| `SM_HIERARCHY` | 4 | Rule 3 |
| `SM_PAIR` | 8 | Rule 4 |
| `SM_BIGX` | 16 | Rule 5 |
| `SM_HARDBLANK` | 32 | Rule 6 |
| `SM_KERN` | 64 | Kerning (fit without combining visible glyphs) |
| `SM_SMUSH` | 128 | Allow sub-characters to occupy one column |

`standard.flf` begins `flf2a$ 6 5 16 15 46 0 24463 229`. After the `flf2a` magic is stripped, hardblank is `$`, print direction is `0`, and full layout is `24463`. The low 8 bits are `143` (`0b10001111`): `SM_EQUAL | SM_LOWLINE | SM_HIERARCHY | SM_PAIR | SM_SMUSH`. Rule 5, rule 6, and `SM_KERN` are clear in that byte. Higher bits of `24463` are not read by `smushChars` or `smushAmount`. If a font header has no full-layout field, `loadFont` derives one from the old-layout field: `0` becomes `64` (kern only), a negative value becomes `0`, and any other value becomes `(oldLayout & 31) | 128`.

`smushAmount` decides how many columns the new glyph may slide into the current row. `smushRow` then walks that overlap from the left and replaces each overlapped column with `smushChars(left, right)`. The row becomes `addLeft + addRight[maxSmush:]`.

`smushChars` applies these gates, in order, before any of the six rules:

1. A space on the left returns the right character. A space on the right returns the left character. This happens for every mode, including kerning-only and mode `0`.
2. If `prevCharWidth < 2` or `curCharWidth < 2`, it returns `None`. Equal letters do not combine when either glyph is narrower than 2. The space case above has already returned.
3. If `SM_SMUSH` is clear, it returns `None`. Visible sub-characters are not combined. `SM_EQUAL` without `SM_SMUSH` still returns `None` for `'A'+'A'`.
4. If `smushMode & 63 == 0` (none of the six rule bits) and `SM_SMUSH` is set, universal overlap is used instead of the six rules. A hardblank yields to the other character. Otherwise left-to-right keeps the right character and right-to-left keeps the left character. With the right-to-left swap in `smushRow`, that prefers the later character of the user’s text. Measured with hardblank `$`: `'A'+'B'` → `'B'` left-to-right and `'A'` right-to-left; `'$'+'B'` → `'B'`; `'A'+'$'` → `'A'`.

The pairs below were produced by calling `FigletBuilder.smushChars` with that rule’s bit, `SM_SMUSH`, hardblank `$`, and both character widths at least 2. The one-row results were produced by `smushAmount` plus `smushRow` on a one-line buffer. `None` means the edges do not overlap.

When several rule bits are set, the code checks hardblank, then equal characters, then the lowline/hierarchy table (lowline first), then opposite pairs, then big-X.

### Rule 1 — `SM_EQUAL` (1)

Two identical sub-characters become that character. Hardblanks do not take this path: a hardblank on either side returns `None` before the equality test, unless rule 6 has already accepted a hardblank pair.

| Left | Right | Result |
| --- | --- | --- |
| `A` | `A` | `A` |
| `A` | `B` | `None` |
| `_` | `_` | `_` |
| `$` | `$` | `None` |

One-row fit, amount 1: `'AA' + 'AA'` → `'AAA'`. The touching `A` columns become one `A`. `'AB' + 'BA'` → `'ABA'`, because the touching letters are the equal `B`s.

With rules 1 and 2 both enabled, `'_'+'_'` still returns `'_'` (equality wins). `'_'+'|'` returns `'|'` (lowline).

### Rule 2 — `SM_LOWLINE` (2)

`'_'` smushes with a character in `|/\[]{}()<>`. The other character is kept. The pair `'_'+'_'` does not match this rule. A character outside that set, such as `'A'`, does not match.

- `'_' + '|'` → `'|'`
- `'_' + '/'` → `'/'`
- `'_' + '\\'` → `'\\'`
- `'_' + '['` → `'['`
- `'_' + ']'` → `']'`
- `'_' + '{'` → `'{'`
- `'_' + '}'` → `'}'`
- `'_' + '('` → `'('`
- `'_' + ')'` → `')'`
- `'_' + '<'` → `'<'`
- `'_' + '>'` → `'>'`
- `'|' + '_'` → `'|'`
- `'_' + 'A'` → `None`
- `'_' + '_'` → `None`

One-row fit, amount 1: `'__' + '||'` → `'_||'`. The touching `'_'` and `'|'` become `'|'`.

### Rule 3 — `SM_HIERARCHY` (4)

Six classes, earlier to later: `|`, `/\`, `[]`, `{}`, `()`, `<>`. The table in `smushChars` is:

```text
('|',  '/\[]{}()<>')
('/\', '[]{}()<>')
('[]', '{}()<>')
('{}', '()<>')
('()', '<>')
```

If the two characters fall in different classes, the one from the later class is returned, from either side. Two characters in the same class do not match, so opposite brackets and opposite slashes are left to later rules.

- `'|' + '/'` → `'/'`
- `'/' + '|'` → `'/'`
- `'/' + '['` → `'['`
- `'[' + '/'` → `'['`
- `'[' + '{'` → `'{'`
- `'{' + '['` → `'{'`
- `'{' + '('` → `'('`
- `'(' + '{'` → `'('`
- `'(' + '<'` → `'<'`
- `'<' + '('` → `'<'`
- `'/' + '\\'` → `None`
- `'[' + ']'` → `None`
- `'<' + '>'` → `None`

One-row fit, amount 1: `'||' + '//'` → `'|//'`. The touching `'|'` and `'/'` become `'/'`.

With rules 3 and 4 both enabled, `'['+'{'` returns `'{'` (hierarchy). `'['+']'` returns `'|'` (pair; hierarchy does not match that pair).

### Rule 4 — `SM_PAIR` (8)

`[]`, `{}`, and `()` in either order become `'|'`. The code checks `left+right` and `right+left` against `['[]', '{}', '()']`. `<>` is not a pair here. A mixed pair such as `[` + `}` does not match.

- `'[' + ']'` → `'|'`
- `']' + '['` → `'|'`
- `'{' + '}'` → `'|'`
- `'}' + '{'` → `'|'`
- `'(' + ')'` → `'|'`
- `')' + '('` → `'|'`
- `'<' + '>'` → `None`
- `'>' + '<'` → `None`
- `'[' + '}'` → `None`

One-row fit, amount 1: `'[[' + ']]'` → `'[|]'`.

### Rule 5 — `SM_BIGX` (16)

`smushChars` returns:

- `'/' + '\\'` → `'|'`
- `'\\' + '/'` → `'Y'`
- `'>' + '<'` → `'X'`
- `'<' + '>'` → `None`
- `'/' + '/'` → `None`

The comment on the constant says `/ + \ -> X, > + < -> X`. The function returns `'|'` for `'/'+'\\'`, returns `'Y'` for `'\\'+'/'`, and handles `'>'+'<'` only. `'<'+'>'` returns `None`.

One-row fits, amount 1:

- `'//' + '\\'` → `'/|\\'`
- `'\\' + '//'` → `'\\Y/'`
- `'>>' + '<<'` → `'>X<'`

With rules 3 and 5 both enabled, `'/'+'\\'` still returns `'|'` and `'\\'+'/'` returns `'Y'`, because hierarchy does not match those same-class pairs.

### Rule 6 — `SM_HARDBLANK` (32)

If both characters are the font’s hardblank, the left character (that hardblank) is returned. If only one side is a hardblank, `smushChars` returns `None`, so a hardblank does not merge with a visible sub-character under this rule. That early return is also why rule 1 does not smush two hardblanks.

With hardblank `$`:

| Left | Right | Result |
| --- | --- | --- |
| `$` | `$` | `$` |
| `$` | `A` | `None` |
| `A` | `$` | `None` |

One-row fit, amount 1: `'$$' + '$$'` → `'$$$'`.

`replaceHardblanks` later turns the font hardblank into a normal space in the output string. With rules 6 and 1 both enabled, `'$'+'$'` still returns `'$'` (rule 6 runs first) and `'A'+'A'` returns `'A'`.

### Kerning

Kerning is the horizontal fit in `smushAmount`, controlled by `SM_KERN` (64) together with `SM_SMUSH`.

If neither bit is set, `smushAmount` returns `0`. Rows are concatenated. Measured: mode `0`, `'AB  ' + '  CD'` stays `'AB    CD'` (amount 0).

If `SM_KERN` is set and `SM_SMUSH` is not, `smushAmount` still computes a slide, but `smushChars` refuses to combine two visible sub-characters. For each row the slide is the gap between the last non-space of the left row and the first non-space of the right row (only the ASCII space `' '` is stripped). The minimum across rows is used, and the result is capped by the current glyph’s width. The extra `+ 1` that overlaps the two edge characters is added only when the left edge is empty or a space, or when `smushChars` returns a character. Under kerning-only, two visible edges do not get that extra column, so the glyphs move together until they touch.

Measured with mode `64`, widths 4, one row: `'AB  ' + '  CD'` → amount 4 → `'ABCD'`. The four spaces between `B` and `C` collapse. `B` and `C` are not replaced. During that slide, space columns still resolve by the space rule (`' '` + `'C'` → `'C'`, `'B'` + `' '` → `'B'`).

On the first character the buffer rows are empty. The same formula yields amount 0 for a glyph with no leading spaces, so the first glyph is placed as stored.

`SM_KERN` combined with `SM_SMUSH` and with no rule bits is universal overlap, not kern-only: `'AB' + 'CD'` → `'ACD'` (amount 1, right edge `C` replaces `B`).

## 5. CLI options `-f`, `-w`, `-j`, `-D`, `-r`, `-F`, `-s`, `-n`

`main()` uses `OptionParser`. The rendered text is `' '.join(args)`. `Figlet.renderText` builds the art, then the flags below are applied in this order: `-r`, then `-F`, then `-s` or else `-n`. `main()` always writes the resulting bytes and then one more `b'\n'`.

### `-f` / `--font`

Font name. Default: `standard` (`DEFAULT_FONT`). Passed to `Figlet(font=...)`.

`preloadFont` tries `{font}.tlf` and then `{font}.flf`. For each name it checks the `pyfiglet.fonts` package. If that resource is missing, it looks in `./` and then `FONT_DIRECTORIES` (`/usr/local/share/pyfiglet/`, `/usr/local/share/figlet`, `/usr/share/figlet` on non-Windows; `%APPDATA%\pyfiglet` on Windows). A hit inside the package stops the search. A hit in the fallback directories does not stop the extension loop, so a later `.flf` replaces an earlier fallback `.tlf`. A packaged `.tlf` is kept, because that branch `break`s. Missing font: `FontNotFound`, and `main()` prints `pyfiglet error: requested font '…' not found.`

### `-w` / `--width`

Integer column width. Default `80`. Stored on `Figlet` and copied to `FigletBuilder.width`.

For each character, `currentTotalWidth = len(buffer[0]) + curCharWidth - maxSmush`. When that is at least `width`, `handleNewLine` wraps. If a space was seen, the buffer saved at the last space is emitted and the iterator rewinds to that space. If no space was seen, the current buffer is emitted and the iterator moves back one character so the glyph is retried on the next line. An explicit `\n` uses the same flush.

If `width` is less than the current glyph’s width, `addCharToProduct` raises `CharNotPrinted("Width is not enough to print this character")`. `main()` does not catch that exception.

The same width is the justification width (see `-j`).

### `-j` / `--justify`

Choices: `auto` (default), `left`, `center`, `right`. The help text says justification defaults to the print direction.

`Figlet.justify` maps `auto` to `left` when direction is left-to-right, and to `right` when direction is right-to-left. `justifyString` then:

- `right`: prepend `width - len(row) - 1` spaces. For width 10 and row `ABCD`, that is five spaces: `'     ABCD'` (length 9).
- `center`: prepend `int((width - len(row)) / 2)` spaces. Width 10 and `ABCD` → `'   ABCD'` (length 7).
- any other value, including `left`: the row is unchanged.

### `-D` / `--direction`

Choices: `auto` (default), `left-to-right`, `right-to-left`.

`auto` reads the font header’s print-direction field (`FigletFont.printDirection`). `0` and any value other than `1` (including a missing field) select left-to-right. `1` selects right-to-left. `standard.flf` stores `0`.

In `smushAmount` and `smushRow`, right-to-left swaps the current row buffer with the new glyph before measuring and overlapping, then appends the unconsumed tail. Universal overlap keeps the later character of the input text, as described in section 4. `auto` justification follows this direction.

### `-r` / `--reverse`

Sets `opts.reverse`. After rendering, `FigletString.reverse` translates each row with `__reverse_map__` and then reverses the row.

In the ASCII range the map mirrors brackets and slashes: `(`↔`)`, `/`↔`\`, `<`↔`>`, `[`↔`]`, `{`↔`}`. Letters, digits, `_`, `|`, `^`, and space stay themselves.

Measured: `FigletString('(ab/\\<>[])\n').reverse()` is `'([]<>/\\ba)\n'`. `FigletString('A_^/\\\n').reverse()` is `'/\\^_A\n'`.

### `-F` / `--flip`

Sets `opts.flip`. `FigletString.flip` reverses the row order, and each row is translated with `__flip_map__`.

In that map, `/`↔`\`, `A`→`V`, `V`→`A`, `M`→`W`, `W`→`M`, `^`→`v`, `_`→`-`, `b`→`P`, `P`→`b`, `u`→`^`, `v`→`m`, `m`→`w`. `<` and `>` are unchanged. `R`→`b` as well.

Measured on one row (row order does not change): `FigletString('A_^/\\\n').flip()` is `'V-v\\/\n'`. `FigletString('(ab/\\<>[])\n').flip()` is `'(aP\\/<>[])\n'`.

If both `-r` and `-F` are set, `main()` reverses first and flips the reversed string.

### `-s` / `--strip-surrounding-newlines`

`FigletString.strip_surrounding_newlines` walks `splitlines()`. Leading rows for which `row.strip() == ''` are dropped. Once a row with a non-space character has been seen, later rows are kept, including internal blank lines. Rows are not individually stripped, so leading spaces on the first kept line stay. The kept lines are joined with `'\n'.join(...) + '\n'`, then `str.rstrip()` removes trailing whitespace. That deletes trailing blank lines and also trailing spaces on the last kept line.

Measured input `'\n\n  hi\n\nthere  \n\n'` becomes `'  hi\n\nthere'`. Input `'  x  \n\n'` becomes `'  x'`.

`main()` then writes one trailing newline, so the last line is terminated without an extra blank line.

### `-n` / `--normalize-surrounding-newlines`

`normalize_surrounding_newlines` returns `'\n' + strip_surrounding_newlines() + '\n'`. The same input becomes `'\n  hi\n\nthere\n'`.

`-s` and `-n` are `if` / `elif`. When both are passed, only `-s` runs.

`main()` appends another newline after that string. Together with the newline `normalize` already added, the output has one empty line before the art and one empty line after it.
