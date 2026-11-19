# Ayush Khurana — Harbor practice task: `titlecase-go`

Port [python-titlecase](https://github.com/ppannuto/python-titlecase) (MIT, SHA `42f43e2`, v2.4.1) to a
Go 1.23 standard-library program whose output matches the original `titlecase()` byte for byte.

## Results

| Run | reward | build | no_python | no_exec | behaviour | Evidence |
|---|---|---|---|---|---|---|
| oracle | **1.0** | 1.0 | 1.0 | 1.0 | 1.0 | `results/oracle.*.json` |
| nop | **0.0** | 0.0 | 0.0 | 0.0 | 0.0 | `results/nop.*.json` |
| cheat (prints memorised visible answers, obeys every hard rule) | **0.0** | 1.0 | 1.0 | 1.0 | 0.0 | `results/cheat.*.json` |

Extra cheats, run against the real grader with `extra-cheat-tests/try_verifier.sh`:
echo input 0.0225, read `/tests` at grading time 0.0, hand off to another program via `os/exec` 0.0.

## Two lines

1. Hardest rules: places where Python's regex is Unicode-aware and Go's is ASCII-only (no-break spaces are
   whitespace; `İ ı ſ K` match `i/s/k` under `re.IGNORECASE`), and order-dependent side effects
   (`AT&T` -> `At&T` as first word, `q&a` -> `Q&A` as last word, `v.` swallowing its own period).
   The reference port passed 4,000/4,000 lines and still failed a 30,000-line fuzz test until fixed.
   (Found while building and fuzzing the oracle, not from an independent agent run.)
2. To make it harder: a second mode frozen with the `regex` library installed (`\p{...}` classes), or
   requiring the custom wordlist callback.

## Design choices that differ from the Day 3 guide

- **Hard rules are gates, not points**: `reward = behaviour`, and behaviour is 0 unless build, no_python
  and no_exec all pass. With the guide's 1/1/4 weights, a cheat that builds and deletes `.py` scores 0.33.
- **no_exec rule** (no `os/exec`, `syscall`, `unsafe`, `os.StartProcess`, `go:linkname`; cgo off): the
  agent image contains `python3`, so otherwise a Go program could run the Python source as a string.
- **Grading as `nobody`**: the agent's program cannot read `/tests` (root-only) during grading.
- **Reward Kit criteria live in `tests/checks/`**, because Reward Kit executes every `.py` in the folder it
  is given; `tests/gen.py` would otherwise run inside the grader.
- **Answers frozen with the container's own Python 3.11.2** (the agent can run it), pinned base image by
  digest, `GOTOOLCHAIN=local`, `artifacts = ["/workspace/repo"]` for the separate verifier.

## Reproduce

```
harbor run -p ./titlecase-go -a oracle      # 1.0
harbor run -p ./titlecase-go -a nop         # 0.0
# cheat: copy titlecase-go/cheat/solve.sh over solution/solve.sh, run -a oracle, then restore  -> 0.0
# answer sheet: cd titlecase-go && docker build -t titlecase-go-env environment &&
#   docker run --rm -v "$PWD:/task" -w /task titlecase-go-env python3 -B tests/gen.py   (deterministic)
```

`NOTES.md` = author notes: every rule with real outputs, surprises, frozen hashes, oracle findings.
