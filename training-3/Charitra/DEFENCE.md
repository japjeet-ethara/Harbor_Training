# Day 6 — security proof and defence

## Proof status

The hardened 100k exam uses frozen stdlib-`re` answers and verifies each candidate in an isolated fresh-UID worker. Harbor evidence shows the Day 6 oracle at 1.000, nop at 0.000, and Yugal's three cheats at 0.0486, 0.1646, and 0.000.

| Candidate | Required | Observed | Evidence |
|---|---:|---:|---|
| Oracle | 1.000 | 1.000 | `proof/oracle-reward.json` |
| Nop | 0.000 | 0.000 | `proof/nop-reward.json` |
| Yugal cheat 1 | <0.2 | 0.0486 | `proof/day5-cheat1-reward.json` |
| Yugal cheat 2 | <0.2 | 0.1646 | `proof/day5-cheat2-reward.json` |
| Yugal cheat 3 | <0.2 | 0.000 | `proof/day5-cheat3-reward.json` |

Harbor job folders are under `jobs/day5-20261120/`. The checked-in reward and grade-detail JSON files are copied into `proof/` so the scores remain available when local job output is omitted from Git.

## Before/after score table

| Check | Original 2k exam | Hardened 100k exam |
|---|---:|---:|
| Oracle | 1.000 | 1.000 |
| Nop | 0.000 | 0.000 |
| Yugal cheat 1 — lookup | 0.351 | 0.0486 |
| Yugal cheat 2 — half port | 0.3717 | 0.1646 |
| Yugal cheat 3 — Python wrapper | 1.000 | 0.000 |
| MadhurJain port exact accuracy | 64.400% | 91.248% |
| LokeshDeshwal port exact accuracy | 34.900% | 86.753% |

The classmates' percentages are byte-exact match rates on the separate old and new datasets; they are not Harbor rewards. Full counts are in `measure/RESULTS.md`.

## Five-minute defence talk

**0:00–0:45 — The attack.** Yugal's strongest cheat wrapped the original Python titlecaser in a Go launcher. It earned 1.000 because Python was installed in the candidate runtime and the old no-Python test only looked for `.py` filenames. Two other cheats showed that build and no-Python points created a 0.333 floor before useful behavior.

**0:45–1:45 — What changed.** I gave behavior 5.8 of the 6 total reward weight, leaving build and no-Python at 0.1 each. I removed interpreter directories from the candidate PATH and reject root Go imports of `os/exec` and `syscall`. The hidden scorer still runs the candidate in a fresh-UID worker and reads the frozen answer file outside the candidate's access.

**1:45–2:45 — The new exam.** I generated 100,000 deterministic inputs with seed 1, froze answers in two separate Python hash-seed runs, kept records whose output agreed, and confirmed the optional regex module was absent. All 100,000 records were stable. The inputs and answers are hash-pinned in `tests/data/manifest.json`.

**2:45–3:45 — Before and after.** Use the before/after table above. The lookup fell from 0.351 to 0.0486, the half port from 0.3717 to 0.1646, and the Python wrapper from 1.000 to 0.000. Oracle stayed at 1.000 and nop stayed at 0.000. The table also shows the two classmates' exact match rates on both exams.

**3:45–4:30 — The comparison.** On the same 100k answers, Charitra's solution matched all records; MadhurJain's port missed 8,752 and LokeshDeshwal's missed 13,247. This confirms the exam still distinguishes a complete port from plausible but incomplete implementations.

**4:30–5:00 — Surprise and close.** The surprise was that changing only the reward weights cut the lookup score sharply, while the half port still reached 0.1646, close to the 0.2 ceiling. That's why the score change is paired with the Go-only runtime and direct process-execution checks. The oracle retained full credit after hardening.
