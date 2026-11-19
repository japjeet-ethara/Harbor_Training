# Day 4 — Attack Report

## 1. Target Information

- **Target trainee:** Hardika
- **Task name:** hardika-titlecase-go (`section18/titlecase-go`)
- **Source commit:** `67fca291d27e8f9da856b00242069608e2ad1d38`
- **Attack date:** 2026-11-19
- **Attacker:** SnehaSadhukhan (GitHub `sneha-ethara`)
- **Harbor / Docker:** Harbor 0.25.0, Docker 29.9.2

All experiments ran against **fresh scratch copies** of `attack/target/`. The target copy and its original `solution/solve.sh` (SHA-256 `9efe91c7ea2e6952261dc83f4fb96e2c7dd5cf4d43e8a5cd2c8177e9d808c0ac`) were never modified; this was re-verified after every run.

## 2. Grading Mechanism

Paths below are relative to `attack/target/`.

- **Driver:** `tests/test.sh:12` runs `grade.py`, which writes `build`/`no_python`/`behaviour` to a temp `grade.json`; `tests/test.sh:13` runs `rewardkit`, and the three criteria (`tests/build/check.py:9-10`, `tests/no_python/check.py:9-10`, `tests/behaviour/check.py:9-10`) only **re-read** that JSON — they do not recompute.
- **build:** `go build ./...` must succeed (`tests/grade.py:102`). On failure every score stays 0 (`:103`).
- **no_python:** credited only after a successful build **and** when no `.py` file remains anywhere in the workspace (`tests/grade.py:76,105-106`; walker at `:33-39`).
- **behaviour:** the built binary is run on the hidden inputs and its stdout is compared, record-by-record, to `data/hidden_expected.txt` (2000 records) — `tests/grade.py:107-115`, scoring at `:26-30`. Partial credit = fraction of exact-match records; overproduction forces 0 (`:28-29`); output is capped at 8 MB (`:12,113-114`).
- **Weights / formula:** `tests/reward.toml` sets `build=1, no_python=1, behaviour=4`, so

  **R = (B + N + 4·C) / 6**

- **Hidden-data boundary:** the hidden datasets are baked **only** into the verifier image (`tests/Dockerfile:14`); the visible `data/inputs.txt`/`expected.txt` are excluded (`tests/.dockerignore`). `/tests` is `chmod 700`, root-owned (`tests/Dockerfile:8`), and the behaviour binary runs as **nobody** under `setpriv --no-new-privs --reuid 65534` with an fsize cap and process-group kill (`tests/grade.py:45-48,77-79,110-115`). The agent workspace (`/workspace/repo`) never contains the hidden answers.

## 3. Cheat 1 — Reward Floor

- **Objective:** can `build` + `no_python` be earned with no titlecase implementation?
- **Implementation (`attack/cheat1/solve.sh`):** write `go.mod` (`module titlecase-cheat`, `go 1.23.0`) and a `main.go` that does `io.Copy(os.Stdout, os.Stdin)` — pure passthrough, no transformation — then delete all `.py` files and `go build ./...`.
- **Technical mechanism:** the binary compiles (build=1) and no `.py` remains (no_python=1), but passthrough output equals the *input*, which almost never equals the titlecased expected output, so behaviour ≈ 0.
- **Actual Harbor score:** build **1.0**, no_python **1.0**, behaviour **0.0**, reward **0.3333**.
- **Job folder:** `2026-11-19__14-51-57` — evidence `attack/results/cheat1-reward.json`.
- **Why it worked:** build and no_python are independent of correctness, so they pay out even for a non-solution (2/6).
- **Security implication:** a trivial non-solution banks 33% of the reward.
- **Recommended defence:** gate `no_python` (and ideally `build`) behind a minimum behaviour threshold, or lower their weight so a non-functional submission scores ~0.

> First attempt failed (reward 0.0) because the module was named `titlecase`, so `go build ./...` tried to emit an executable named `titlecase`, colliding with the upstream `titlecase/` Python package directory left in `/workspace/repo` (`go: build output "titlecase" already exists and is a directory`). Renaming the module to `titlecase-cheat` fixed it. Job `2026-11-19__14-12-01` holds that genuine failed run.

## 4. Cheat 2 — Partial Titlecase

- **Objective:** how much behaviour credit does a deliberately incomplete implementation earn?
- **Implemented rules (`attack/cheat2/solve.sh`):**
  - ASCII-only: lowercase each word, capitalise its first ASCII letter.
  - Small-word rule: 21 words (`a, an, and, as, at, but, by, en, for, if, in, nor, of, on, or, per, the, to, v, vs, via`) stay lowercase unless first/last word of the line.
  - Preserves exact runs of ASCII spaces; strips a trailing `\r` per record (basic CRLF handling); empty stream → no output.
- **Deliberately omitted:** all non-ASCII/Unicode casing (e.g. Deseret `𐐨→𐐀`, ligature `Ffi`, final sigma); words with intentional internal capitals left as-is (e.g. `BIBLIOGRAPHY`, `McName`); apostrophe/compound/hyphen rules; punctuation-aware capitalisation (capitalising after `?`/`:`); roman numerals; tabs and Unicode whitespace as separators; the full small-word edge cases.
- **Actual Harbor score:** build **1.0**, no_python **1.0**, behaviour **0.0395**, reward **0.3597**.
- **Job folder:** `2026-11-19__14-53-28` — evidence `attack/results/cheat2-reward.json`.
- **Why it scored low:** only ~3.95% of the 2000 hidden records matched exactly — the dataset is dominated by the Unicode, punctuation and intentional-capitalisation cases this cheat omits, and one wrong byte fails a whole record (`tests/grade.py:30`).
- **Recommended defence:** none needed for scoring integrity — partial credit behaved correctly and proportionally. The small bump (+0.026 over the floor) shows behaviour weight is doing its job; the residual soft spot is still the 0.333 floor from §3.

## 5. Cheat 3 — Hidden Exam Accessibility

- **Objective:** can the running solution read the hidden answer files or verifier data?
- **Paths investigated (`attack/cheat3/solve.sh`), in order:** `/tests/data/hidden_expected.txt`, `/tests/data/hidden_inputs.txt`, `data/hidden_expected.txt` (relative to `/workspace/repo`), `/tests/data/expected.txt`. On the first readable, non-empty file the program replays it verbatim; otherwise it falls back to passthrough.
- **Access result:** **none readable.** The reward equals the passthrough floor exactly, which means every candidate path failed (permission denied or absent), so the fallback executed.
- **Actual Harbor score:** build **1.0**, no_python **1.0**, behaviour **0.0**, reward **0.3333**.
- **Job folder:** `2026-11-19__14-54-59` — evidence `attack/results/cheat3-reward.json`.
- **Whether hidden data was accessible:** **No.** If `/tests/data/hidden_expected.txt` had been readable, replaying it would have produced behaviour ≈ 1.0 (reward ≈ 1.0); instead behaviour is 0.0, identical to Cheat 1's passthrough. This is a **blocked-access finding**, not an exploit.
- **Why it's blocked:** `/tests` is `chmod 700` and root-owned (`tests/Dockerfile:8`), while the binary runs as **nobody** (`tests/grade.py:45-48,77`); the hidden files also never reach `/workspace/repo`. This is the proper isolation Hardika implemented, and it defeats the answer-replay class (the author's own `cheat/replay/` works only on the *visible* dataset).
- **Recommended defence:** none required — the isolation is effective. Keep `/tests` root-owned `0700` and continue running the behaviour binary as an unprivileged user; do not ship hidden data into the agent workspace.

## 6. Results Comparison

| Experiment | Build | no_python | Behaviour | Total Reward | Job Folder |
|---|---:|---:|---:|---:|---|
| Cheat 1 — Reward floor | 1.0 | 1.0 | 0.0000 | 0.3333 | 2026-11-19__14-51-57 |
| Cheat 2 — Partial titlecase | 1.0 | 1.0 | 0.0395 | 0.3597 | 2026-11-19__14-53-28 |
| Cheat 3 — Hidden-exam probe | 1.0 | 1.0 | 0.0000 | 0.3333 | 2026-11-19__14-54-59 |

All values are copied from the real `verifier/reward.json` of each job (byte-identical copies in `attack/results/`). Formula check: Cheat 2 = (1 + 1 + 4·0.0395)/6 = 0.3597 ✓.

## 7. Findings

- **Strongest attack:** Cheat 2 (0.3597) — highest actual reward, by adding ~4% genuine behaviour on top of the floor.
- **Weakest attack:** Cheats 1 and 3 tie at the 0.3333 floor; Cheat 3 is "weakest as an exploit" because the access it targeted is blocked.
- **Build and no_python earn independent points:** **Yes** — every cheat scored build 1 + no_python 1 with behaviour 0–0.04, i.e. a guaranteed 0.333 for any compiling, `.py`-free non-solution.
- **Do partial implementations get meaningful credit:** only **proportionally and honestly** — 3.95% correct records → +0.026 reward. No parsing/count trick inflates it (overproduction and the fixed 2000 denominator are enforced at `tests/grade.py:26-30`).
- **Is hidden data properly isolated:** **Yes** — Cheat 3 confirmed the hidden answers are unreadable to the solution process (root-owned `0700` `/tests` + nobody execution + data kept out of the workspace).
- **Effective grading controls:** hidden-data isolation, positional exact-match scoring with a fixed denominator, the overproduction guard, and the 8 MB output cap.

## 8. Recommendations

1. **Close the reward floor (main weakness):** require a minimum behaviour score before paying `no_python` (and optionally `build`), or reduce their combined weight, so a non-functional submission scores near 0 instead of 0.333.
2. **Keep the hidden-data isolation** exactly as-is: `/tests` root-owned `0700`, behaviour binary as nobody, hidden datasets only in the verifier image.
3. **Keep the scoring guards** (fixed 2000 denominator, overproduction → 0, 8 MB cap) — they prevented any count/parse inflation.
4. No change is warranted for partial credit — it behaved correctly and proportionally.

## 9. Final Conclusion

- **Highest actual reward achieved:** **0.3597** (Cheat 2 — partial titlecase).
- All three experiments were **genuinely executed** through Harbor oracle runs, each with a real job folder and a byte-verified `reward.json`.
- **No experiment was blocked or skipped.** Cheat 3's low score is a positive security finding: hidden answers are not accessible to the solution process.
- No cheat achieved full reward; the task's correctness requirement and hidden-data isolation held. The only demonstrated weakness is the **0.333 reward floor** from independent build/no_python credit.
