# FIGlet Go port — Harbor Task 2

This task ports pyfiglet to Go and verifies that its rendering and CLI behavior match the original Python implementation byte for byte. Details regarding the upstream source URL, pinned commit, commit date, and licence can be found in [NOTES.md](NOTES.md).

## Results

| Run | Reward | Result | Screenshot |
| --- | --- | --- | --- |
| Oracle | 1.000 | Matched 2,000 of 2,000 hidden cases | [screenshots/oracle.png](screenshots/oracle.png) |
| Nop | 0.000 | The untouched repository did not build as a Go program | [screenshots/nop.png](screenshots/nop.png) |
| Visible-answer cheat | 0.167 | Built successfully and matched 0 of 2,000 hidden cases | [screenshots/cheat.png](screenshots/cheat.png) |

Two generator runs produced byte-identical visible and hidden files, with 2,000 cases in each and 4,000 unique argument lists overall.

## Reflections

- Smushing: I manually checked the equal-character and opposite-pair rules. The first recorded oracle run passed all 2,000 hidden cases. The issue I encountered during generation was an exact-width wrapping loop with ß in the slant font.
- Docker: My first build could not reach Docker Desktop’s Linux engine. I started Docker Desktop, confirmed the Server section with docker version, and reran the build successfully.
