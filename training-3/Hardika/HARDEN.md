# Day 5 — Hardening report (Hardika)

Attacker: Sneha Sadhukhan (`training-3/SnehaSadhukhan/attack/ATTACK.md`, attacked commit `67fca29`).

## Holes closed

All three cheats got 2/6 for free: `build` and `no_python` were paid as soon as the code compiled, even with zero correct titles (`tests/grade.py:105-106` in the original task).

**Fix:** `tests/grade.py` now pays `build` and `no_python` only when at least half of the hidden titles are exact (`GATE = 0.5`). Below the gate a submission earns only `4 × behaviour / 6`, which stays under 0.2 while behaviour is under 0.3. `instruction.md` and `docs/DATASET.md` describe the new rule.

| Cheat | Before (Sneha's Harbor run) | After: expected | After: Harbor job |
|---|---|---|---|
| 1 passthrough | 0.3333 (`2026-11-19__14-51-57`) | 0.0000 | TODO |
| 2 partial port | 0.3597 (`2026-11-19__14-53-28`) | 0.0905 (behaviour 0.1357 on the new exam) | TODO |
| 3 hidden-file probe | 0.3333 (`2026-11-19__14-54-59`) | 0.0000 | TODO |

The "expected" column is NOT a Harbor result. It comes from the measured behaviour numbers (below) put through the new `grade()` logic. The same check reproduces Sneha's "before" numbers exactly (0.3333 and 0.3597). Replace TODO with the real job folders.

**Extra lock (not attacked yet):** the verifier image contains Python, which rewardkit needs. `tests/Dockerfile` now removes access to every Python interpreter for uid 65534 (the user the submitted program runs as). The image build fails if uid 65534 can still start `/usr/local/bin/python3` or `/usr/bin/python3`. TODO: confirm that the image builds and the oracle still scores 1.0.

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
| Kushal Soni | TODO | TODO | TODO |

Raw outputs are in `measure/`. The `*.old-exam.txt` files are the same port on the old 2,000-title exam.

**Madhur's 3,053 are all mode differences.** I froze the same pool a second time without regex (Python's built-in `re`), and Madhur's port got 0 of 100,000 wrong against those answers. Madhur's own instruction says "WITHOUT the optional regex package". The two modes differ on exactly 3,053 of these titles, for example `v1.2` → `V1.2` (regex) vs `v1.2` (re). A port that is correct for its stated mode fails 3% here, which is why `instruction.md` now states the mode in plain words.

**Sneha's cheat 2 measured as a port:** right on 13.6% of the new exam (86,432 of 100,000 wrong) and 4.0% of the old one (1,921 of 2,000 wrong; this matches the 0.0395 in Sneha's Harbor run). Without the gate, the new exam would have *raised* cheat 2 from 0.3597 to 0.4238, because the kit pool has more plain words than the old Unicode-heavy exam.

### How these numbers were made (so they can be re-run)

- Ports were built with Go 1.23.12 and run natively on Windows, not with the guide's `docker run golang:1.23` command, because this PC had no Docker yet. The ports use only stdin/stdout, so the output bytes should match. TODO: re-run one port with the guide's Docker command and confirm.
- Windows Python writes CRLF line endings, so `pool.txt` and the `key/` files were converted to LF afterwards. The two sha256 values above are for the LF files; a Linux run of the kit should give the same hashes.
- On Windows, the kit's child Python prints in cp1252 and crashes on titles like `ıstanbul`. `answers.py` was run unchanged through a small driver that adds `-X utf8` to that child call. That flag has no effect on Linux.
- Kushal's port could not be run on this PC (blocked by the organization's Device Guard policy). TODO: measure it with the guide's Docker command.

## What I learned (3 lines)

TODO: in your own words.
