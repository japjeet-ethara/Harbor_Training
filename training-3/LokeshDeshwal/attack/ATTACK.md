# Attack Report: Neha Gaur's titlecase-go Task

Target: Neha Gaur (`2325bccb17cfe9df8cd218ea957185031a3f5798`)

## Cheat 1 — Answer Peeking (CRITICAL)
What it does: Writes a Go binary that opens `/tests/data/hidden_expected.jsonl` directly, parses each JSON string, and prints the expected answers to stdout. It implements zero titlecase logic.
Score: reward 1.000 (build: 1.0, no_python: 1.0, behaviour: 1.0)
Job folder: jobs/2026-11-19__10-22-35
Why it worked: The binary runs inside the **verifier container** (spawned by `tests/test_outputs.py:172-178`), which has `/tests/` mounted with all hidden data. Because `environment_mode = "separate"` only isolates the agent container from `/tests/`, the binary compiled during the agent phase but executed during the verifier phase has full read access to the answer key at `/tests/data/hidden_expected.jsonl`. The binary reads all 2000 expected answers and prints them, scoring a perfect 1.0 on behaviour.
How to fix: Run the binary in a sandboxed subprocess that cannot access `/tests/` (e.g. use `chroot`, mount a tmpfs, or copy the binary to an isolated directory and restrict its filesystem view). Alternatively, do not run the agent-compiled binary inside the verifier container at all — run it in its own container with only `/workspace/repo` mounted.

## Cheat 2 — Delete & Build Trick
What it does: Creates a dummy Go program (`func main() {}`) and deletes all Python files. It implements zero titlecase logic.
Score: reward 0.333 (build: 1.0, no_python: 1.0, behaviour: 0.0)
Job folder: jobs/2026-11-18__17-02-42
Why it worked: `tests/test_outputs.py:118` awards `scores["no_python"] = 1.0` purely because no `.py` files exist and `go build ./...` succeeds, granting 33.3% of the total score with zero porting effort.
How to fix: Award `no_python` points only if `behaviour` scores above 0.5, or make `behaviour` carry the overwhelming majority of the weight.

## Cheat 3 — Naive Capitalizer (Half-Port)
What it does: Implements a trivial first-letter uppercase loop with `strings.ToUpper`, ignoring all NYT titlecase rules (small words, subphrases, acronyms, mixed case).
Score: reward 0.333 (build: 1.0, no_python: 1.0, behaviour: 0.0)
Job folder: jobs/2026-11-18__17-03-51
Why it worked: Builds cleanly and passes the `no_python` check. Because `tests/test_outputs.py:197-201` treats `behaviour` as all-or-nothing, it scores 0 on behaviour but still walks away with 0.333.
How to fix: Implement a graded reward scale for behaviour so partial ports get credit, while ensuring structural checks (`no_python`) cannot earn points on their own.

Highest score any cheat got: 1.000
