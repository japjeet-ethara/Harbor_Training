# titlecase-go

Harbor task: replace the vendored `python-titlecase` tree with a Go program whose stdin/stdout matches `titlecase()` line for line. The agent prompt is `instruction.md`.

## Environment

- Agent image: `golang:1.23`, workdir `/workspace/repo`, Python sources copied in at build time.
- Verifier image: `tests/Dockerfile` (separate container). It has Go, uv, and Reward Kit. Hidden inputs are baked into that image only.
- Agent timeout 1800s. Verifier timeout 300s. 1 CPU, 2048 MB.

## Verifier

Weighted mean of three programmatic checks:

| Check | Weight | What it measures |
|---|---:|---|
| `build` | 1 | `go build ./...` succeeds |
| `no_python` | 1 | no `.py` files under `/workspace/repo`, and the build still succeeds |
| `behaviour` | 4 | fraction of `/tests/data/hidden_inputs.txt` lines that match `hidden_expected.txt` |

Nothing done scores 0. A build that leaves the Python files in place scores about 0.17. A perfect port scores 1.

Regenerate the frozen answers with `uv run --python 3.12 tools/gen.py`. The script calls the original function; do not edit the answer files by hand.

## Running

```bash
harbor run -p ./titlecase-go -a oracle
harbor run -p ./titlecase-go -a nop
```
