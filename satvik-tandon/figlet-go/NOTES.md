# pyfiglet research

- Source: https://github.com/pwaller/pyfiglet
- Pinned revision: `255827efbc09d662875dad50fa0edc1e1263bf45` (2026-08-02T22:51:18+01:00)
- Licence: MIT.
- A fresh clone cannot find its packaged fonts: `pyfiglet/fonts/` is absent. The Makefile's `minimal` target creates it and copies `pyfiglet/fonts-standard/*` into it.

## Layout rules

Kerning removes adjacent blank columns when a font permits it. The six controlled smushing rules are: equal characters (`|` + `|` becomes `|`); underscore hierarchy (`_` + `/` becomes `/`); hierarchy (`|` + `/` becomes `/`); opposite-pair (`[` + `]` becomes `|`); big-X (`/` + `\\` becomes `|`, `>` + `<` becomes `X`); and hardblank (`$` + `$` remains `$` when enabled). The renderer also has universal smushing, where the later input character wins, plus the special `/` after `\\` result `Y`.

## Options in scope

- `-f`: select a font.
- `-w`: set line width used for wrapping and justification.
- `-j`: `auto`, left, center, or right justification.
- `-D`: automatic, left-to-right, or right-to-left layout direction.
- `-r`: mirror the rendered art horizontally.
- `-F`: flip the rendered art vertically.
- `-s`: strip empty leading and trailing lines.
- `-n`: normalize surrounding newlines to one blank line at each end.

## Reflection for submission

- Smushing difficulty: hardblank handling caused the first visible renderer mismatch; the font header's hardblank marker had to be read correctly and replaced only after layout.
- Docker trap: Harbor needs Bash in the final Alpine image even though Alpine does not include Bash by default; we installed Bash while keeping Python out of the room.
