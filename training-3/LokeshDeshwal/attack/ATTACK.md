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

---

## Day 6 Re-Attack — Neha Gaur's Hardened Task

- **Target:** `training-3/NehaGaur/task` at commit `ceefab5` (*"harden: close cheats 1,2 and 3, 100k exam (separate)"*)
- **Test Engine:** Harbor 0.25.0, 1 trial per run, 0 exceptions

### Re-Attack Score Table

| Cheat / Baseline | Day 4 Score (Before) | Day 6 Score (Hardened) | Harbor Job ID | Status |
| :--- | :---: | :---: | :--- | :--- |
| **Published Oracle** | 1.000000 | **1.000000** | `jobs/2026-11-21__19-53-14` | PASSED (1.000) |
| **Cheat 1 — Answer Peeking** | 1.000000 | **0.000000** | `jobs/2026-11-21__19-54-19` | CLOSED (< 0.20) |
| **Cheat 2 — Delete & Build Trick** | 0.333333 | **0.000000** | `jobs/2026-11-21__19-55-22` | CLOSED (< 0.20) |
| **Cheat 3 — Naive Capitalizer** | 0.333333 | **0.000000** | `jobs/2026-11-21__19-56-23` | CLOSED (< 0.20) |

Reward evidence files: [`attack/results/reattack-cheat1-reward.json`](results/reattack-cheat1-reward.json), [`reattack-cheat2-reward.json`](results/reattack-cheat2-reward.json), [`reattack-cheat3-reward.json`](results/reattack-cheat3-reward.json).

### Defense Verification Analysis
1. **Cheat 1 (Answer Peeking) Neutralized:** Neha restricted permissions on the hidden expected file (`chmod 0600`) and drops process privileges before executing the candidate binary (`os.setgid(65534)`, `os.setuid(65534)` as user `nobody`). When the binary attempts to read `/tests/data/hidden_expected.jsonl`, it fails with `Permission Denied` and produces no output.
2. **Cheats 2 & 3 (Structural Point Exploits) Neutralized:** Neha restructured the composite reward formula:
   $$\text{reward} = \text{scores}[\text{behavior}] \times \frac{\text{scores}[\text{build}] + \text{scores}[\text{no\_python}] + 4}{6}$$
   Because `behavior` score directly multiplies the entire score, solutions that fail behavioral correctness earn an overall reward of `0.000000`, completely eliminating the $0.333$ baseline free credit.
3. **Conclusion:** All three cheats have been successfully driven to `0.000000` (well below the `< 0.20` requirement), while the reference oracle maintains a perfect `1.000000`. Neha Gaur's task is confirmed hardened.
