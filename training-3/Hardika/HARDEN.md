# Day 5 — Hardening report (Hardika)

Attacker: Sneha Sadhukhan (`training-3/SnehaSadhukhan/attack/ATTACK.md`, attacked commit `67fca29`).

## Holes closed

All three cheats got 2/6 for free: `build` and `no_python` were paid as soon as the code compiled, even with zero correct titles (`tests/grade.py:105-106` in the original task).

**Fix:** `tests/grade.py` now pays `build` and `no_python` only when at least half of the hidden titles are exact (`GATE = 0.5`). Below the gate a submission earns only `4 × behaviour / 6`, which stays under 0.2 while behaviour is under 0.3. `instruction.md` and `docs/DATASET.md` describe the new rule.

| Cheat | Before (Sneha's Harbor run) | After (my Harbor run) | Job folder |
|---|---|---|---|
| 1 passthrough | 0.3333 (`2026-11-19__14-51-57`) | **0.0087** (behaviour 0.013, build 0, no_python 0) | `2026-11-23__09-43-38` |
| 2 partial port | 0.3597 (`2026-11-19__14-53-28`) | **0.0905** (behaviour 0.1357, build 0, no_python 0) | `2026-11-23__09-45-25` |
| 3 hidden-file probe | 0.3333 (`2026-11-19__14-54-59`) | **0.0087** (behaviour 0.013, build 0, no_python 0) | `2026-11-23__09-46-28` |

All three are now below 0.2 (Harbor 0.26.0, `--env docker`; details in `proof/cheats-reward.txt`). Cheats 1 and 3 copy the input unchanged; 1.3% of the new titles are already in correct title case, so they earn behaviour 0.013 but nothing else.

**Extra lock (not attacked yet):** the verifier image contains Python, which rewardkit needs. `tests/Dockerfile` now removes access to every Python interpreter for uid 65534 (the user the submitted program runs as). The image build fails if uid 65534 can still start `/usr/local/bin/python3` or `/usr/bin/python3`. The image built and the oracle scored 1.0 with it (job `2026-11-23__09-31-53`).

## Exam: before and after

Old exam: 2,000 hidden titles from `tests/gen.py`. New exam: 100,000 titles, mode: **regex** (regex 2026.11.15, VERSION0).

- Pool: `kit/make_pool.py 100000 1`
- Answers: `kit/answers.py` run twice with different hash seeds. `kit/report.txt`: 100,000 kept, 0 dropped, regex module used True.
- `tests/data/inputs.txt` sha256 `b5b839621b4d7b1e2ddba50e716aa57b6ce437d2ee22777590810d155c72a331`
- `tests/data/answers.txt` sha256 `d4b4ecd7672755caf8f2b5d766c64a5e0a85991a34dfd0d80870c8ae36f02337`

| Port | Wrong on new exam | Old exam caught it? | Chance 2K random misses it |
|---|---|---|---|
| my oracle | 0 of 100,000 | n/a (0 of 2,000 wrong) | n/a |
| Madhur Jain | 3,053 of 100,000 | yes (187 of 2,000 wrong) | 0% |
| Kushal Soni | 3,053 of 100,000 | yes (296 of 2,000 wrong) | 0% |

Raw outputs are in `measure/`. The `*.old-exam.txt` files are the same port on the old 2,000-title exam.

**Both classmates' 3,053 are all mode differences.** I froze the same pool a second time without regex (Python's built-in `re`). Madhur's port and Kushal's port each got 0 of 100,000 wrong against those answers. Madhur's instruction says "WITHOUT the optional regex package"; Kushal's instruction does not name a mode at all. The two modes differ on exactly 3,053 of these titles, for example `v1.2` → `V1.2` (regex) vs `v1.2` (re). A port that is correct for its stated mode fails 3% here, which is why `instruction.md` now states the mode in plain words.

**Sneha's cheat 2 measured as a port:** right on 13.6% of the new exam (86,432 of 100,000 wrong) and 4.0% of the old one (1,921 of 2,000 wrong; this matches the 0.0395 in Sneha's Harbor run). Without the gate, the new exam would have *raised* cheat 2 from 0.3597 to 0.4238, because the kit pool has more plain words than the old Unicode-heavy exam.

### How these numbers were made (so they can be re-run)

- My oracle and Madhur's port were first built with Go 1.23.12 and run natively on Windows. Re-running both with the guide's `docker run golang:1.23` command gave byte-identical output. Kushal's port was measured only with the guide's Docker command.
- Windows Python writes CRLF line endings, so `pool.txt` and the `key/` files were converted to LF afterwards. The two sha256 values above are for the LF files; a Linux run of the kit should give the same hashes.
- On Windows, the kit's child Python prints in cp1252 and crashes on titles like `ıstanbul`. `answers.py` was run unchanged through a small driver that adds `-X utf8` to that child call. That flag has no effect on Linux.
- Native Windows run of Kushal's port was blocked by the organization's Device Guard policy, so it was measured in Docker only.

## Proofs (Harbor 0.26.0, `--env docker`)

| Run | Reward | Job folder |
|---|---|---|
| oracle | 1.0 | `2026-11-23__09-31-53` |
| nop | 0.0 | `2026-11-23__09-42-42` |
| Sneha's cheats | 0.0087 / 0.0905 / 0.0087 | see table above |

## What I learned (3 lines)

1. A check that pays on its own ("it compiles", "no .py files") is free points for a cheat; partial credit must be tied to real correct answers.
2. A bigger exam is not automatically harder: my 100k pool *raised* the half-port cheat until the gate was added, so every exam change has to be re-measured against the cheats.
3. The mode (regex vs re) is part of the answer key: two correct ports disagree on 3% of titles, so `instruction.md` must say which mode is graded.
