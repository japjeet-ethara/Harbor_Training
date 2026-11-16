# pyfiglet Research Notes

- **Upstream Repository:** https://github.com/pwaller/pyfiglet
- **Pinned Commit SHA:** `255827efbc09d662875dad50fa0edc1e1263bf45`
- **Commit Date:** 2024-06-12
- **License:** MIT License

## Font Setup & Packaging Trap
`pyfiglet` stores its standard `.flf` fonts inside `pyfiglet/fonts-standard/` in the Git repository rather than `pyfiglet/fonts/`. Running `pyfiglet` directly from a fresh clone fails with `FontNotFound` unless `fonts-standard/` is copied into `pyfiglet/fonts/`:

```bash
cp -r pyfiglet/fonts-standard pyfiglet/fonts
```

## FLF Header & Hardblank Character
Every `.flf` file begins with a header line starting with `flf2a` immediately followed by the font hardblank character (the 6th character of the header, which varies by font — for example, `$` in `standard.flf` where the header starts with `flf2a$ 6 5 16 15 11 0 24463`). During rendering, hardblanks prevent adjacent sub-characters from smushing through space-replacement and are converted back to normal spaces in the final output.

## Layout Modes, Kerning & Six Smushing Rules
- **Full-width (-1):** Characters are placed side-by-side with zero overlap (example: `A` next to `V` keeps all bounding-box columns separate).
- **Kerning / Fitting (0):** Characters slide horizontally toward each other until two non-space sub-characters touch without overlapping (example: `A` + `V` tuck their diagonal strokes under each other overhang until `/` touches `\`, without merging into one column).
- **Smushing (> 0):** Characters overlap by one additional column when allowed by the font `old_layout` / `full_layout` bitmask:
  1. **Equal Character (1):** Two identical non-hardblank characters smush into one (`|` + `|` -> `|`, `=` + `=` -> `=`).
  2. **Underscore (2):** `_` is replaced by any border character `| / \ [ ] { } ( ) < >` (`_` + `|` -> `|`, `_` + `/` -> `/`, `_` + `[` -> `[`).
  3. **Hierarchy (4):** Ordered classes `|` < `/\` < `[]` < `{}` < `()` < `<>` — the higher class wins (`|` + `/` -> `/`, `/` + `[` -> `[`, `[` + `{` -> `{`, `{` + `(` -> `(`, `(` + `<` -> `<`).
  4. **Opposite Pair (8):** Opposite brackets, braces, or parentheses smush into a vertical bar (`[` + `]` -> `|`, `]` + `[` -> `|`, `{` + `}` -> `|`, `}` + `{` -> `|`, `(` + `)` -> `|`, `)` + `(` -> `|`).
  5. **Big X (16):** Slashes and angle brackets combine (`/` + `\` -> `|`, `\` + `/` -> `Y`, `>` + `<` -> `X`).
  6. **Hardblank (32):** Two hardblanks smush into a single hardblank when universal or rule-based hardblank smushing is enabled (using `standard.flf` hardblank `$`: `$` + `$` -> `$`).

## Supported CLI Options (8 Flags)
- `-f <font>` — Select `.flf` font name (default: `standard`).
- `-w <width>` — Set maximum output width in columns before wrapping (default: `80`).
- `-j <auto|left|center|right>` — Horizontal text justification within the target width (default: `auto`, which selects right-to-left or left-to-right alignment based on print direction).
- `-D <auto|left-to-right|right-to-left>` — Print direction (default: `auto`, inherited from the font `print_direction` header field).
- `-r` — Reverse the rendered output lines horizontally (mirror left-to-right).
- `-F` — Flip the rendered output lines vertically (upside-down).
- `-s` — Strip surrounding newlines from the rendered output.
- `-n` — Normalize surrounding newlines in the rendered output.
