# titlecase-go hand-in

- Repo: https://github.com/ppannuto/python-titlecase
- SHA: `42f43e2de55bf003b286c6f8e8d8b2d26676a167`
- Licence: MIT

## Rewards

| Run | Reward | build | no_python | behaviour |
|---|---:|---:|---:|---:|
| oracle | 1.0 | 1.0 | 1.0 | 1.0 |
| nop | 0.0 | 0.0 | 0.0 | 0.0 |
| cheat A | 0.1667 | 1.0 | 0.0 | 0.0 |
| cheat B | 0.3333 | 1.0 | 1.0 | 0.0 |
| echo | 0.1667 | 1.0 | 0.0 | 0.0 |

Every test line is changed by `titlecase()`. SHA256: `inputs.txt` `BAA61DC1B4410C07C97F44C47FEA521430FE36DD5234F265A20BA212ED8EF984`, `expected.txt` `07D52956F4CBC21B6DA101784CE47CE66EFC0BCBBFE0533A6748A4F4BF5FFFA9`, `hidden_inputs.txt` `8489B5E691350914F90B474E1643403ECE205F931619DACD1159C8344C202A10`, `hidden_expected.txt` `1F519446FB718CE7BCE7FF3374DD7272AE37FD1D23F504C8CF8F3A8BC477E86B`.

With no already-correct hidden line, an echo or a visible-only answer sheet scores behaviour 0. Build alone is 1/6, about 0.1667. Build and no_python together are 2/6, about 0.3333.

The port was not observed to get a titlecase rule wrong: the first comparison against the original matched all 4000 lines. The only failure while building `solution/solve.sh` was `go build ./...` refusing to replace the leftover `titlecase/` directory with the binary of the same name.

Harder task: non-ASCII input, multi-line input with `preserve_blank_lines`, a callback, and fewer already-correct lines.
