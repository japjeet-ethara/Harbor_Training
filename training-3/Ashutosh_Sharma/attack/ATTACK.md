# Attack Report — Harshit Kumar (`75fe6b6208c8c330af9d482ed2034b795d5f13ef`)

## Cheat 1 — Delete Python & Empty Go Stub
What it does:   Deletes all `.py` files in `/workspace/repo`, initializes `go.mod`, and compiles an empty `main.go` (`func main() {}`) with zero titlecase logic.
Score:          reward 0.0000  (build 0, no_python 0, behaviour 0.0)
Job folder:     jobs/2026-11-23__16-49-07
Why it worked:  It did not work (scored 0.0). Both `tests/no_python.py:34-38` and `tests/build.py:27-30` require `go build ./...` with `GOFLAGS=-mod=readonly` (`tests/build.py:13-18`, `tests/no_python.py:13-18`) to pass before awarding points, preventing trivial file-deletion or unverified stub shortcuts.
How to fix:     Keep the coupled `_build_ok()` check in `tests/no_python.py:36` and consider requiring `behaviour > 0` before awarding `build` or `no_python` points so even a valid empty binary cannot earn `2/12` (`0.1667`).

## Cheat 2 — Runtime Filesystem Read of Hidden Expected Answers
What it does:   Compiles a Go binary that reads `/tests/data/hidden_expected.txt` directly from disk at runtime (with a `filepath.WalkDir` fallback) and prints its exact bytes to stdout instead of computing titlecase.
Score:          reward 0.8333  (build 0, no_python 0, behaviour 1.0 -> 10/12 weighted mean)
Job folder:     jobs/2026-11-23__16-50-18
Why it worked:  `tests/behaviour.py:9-10` stores the ground-truth file at `/tests/data/hidden_expected.txt` inside the container during verification, and `tests/behaviour.py:72-77` executes the untrusted `/tmp/tc` binary with full read permissions on `/tests/data/hidden_expected.txt`, giving `1.0` on `behaviour` (`weight = 10` in `tests/reward.toml:4`).
How to fix:     Run `/tmp/tc` as an unprivileged non-root user (`nobody`) with `chmod 700 /tests` so the compiled binary cannot read `/tests/data/hidden_expected.txt`, or pass inputs in randomized batches/process invocations rather than static pre-mounted files readable by the binary.

## Cheat 3 — Naive 25-Line Half-Port (Space-Split & Small-Word Map Only)
What it does:   Implements a minimal ~25-line Go program that only splits on ASCII spaces and lowercases interior small words, ignoring punctuation, hyphens, slashes, `Mc-` names, acronyms, internal capitals, and tabs.
Score:          reward 0.0000  (build 0, no_python 0, behaviour 0.0)
Job folder:     jobs/2026-11-23__16-51-19
Why it worked:  It did not work (scored 0.0). `tests/gen.py:19-55` and `tests/gen.py:269-329` enforce at least 12 occurrences of punctuation, slashes, hyphens, `Mc-`, and tabs per set, and `tests/behaviour.py:31-44` requires exact byte-for-byte line matches across `hidden_expected.txt`.
How to fix:     Expand `tests/gen.py:9` from `COUNT = 2000` to `100,000` inputs and include edge cases currently excluded by `tests/gen.py:182-186` (empty lines, NBSP, CRLF, and non-Latin Unicode such as `ıstanbul`).

Highest score achieved by any cheat: **0.8333** (Cheat 2 — Runtime Filesystem Read of Hidden Expected Answers)