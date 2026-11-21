# HARDEN.md

## Holes closed

Cheat 1 — Python inside: 1.0, now 0.1667 (rerun: `jobs/2026-11-20__14-44-14`)

Fix: restricted Python in the verifier image and extended `no_python` to reject Go source that shells out to Python or uses executable/process APIs. The 100K exam also removes all visible answer overlap.

Cheat 2 — Lookup table: 0.5682, now 0.1765 (rerun: `jobs/2026-11-20__14-46-14`)

Fix: replaced the 2,000-line overlapping pool with 100,000 frozen non-overlapping weird inputs and rejected lookup-table patterns in `no_python`.

Cheat 3 — Read the exam: 0.3337, now 0.1667 (rerun: `jobs/2026-11-20__14-48-10`)

Fix: answer files are 0600, there is no visible/stale answer file, and `no_python` rejects filesystem answer-search patterns.

## Exam: before and after

Old exam: 2,000 inputs.

New exam: 100,000 inputs. Mode: **titlecase WITHOUT regex**. Frozen twice: 100,000 kept, 0 dropped.

| Port | Wrong on new exam | Wrong on old exam |
|---|---:|---:|
| my oracle | 0 / 100,000 | 0 / 2,000 |
| SaurabhBaghel | 6,650 / 100,000 | 0 / 2,000 |
| Yuvraj-Singh | 4,027 / 100,000 | 0 / 2,000 |

The old exam did not reveal either classmate's errors; see the `*-old.txt` measurement files.

Final Harbor oracle reward: 1.0 (job `jobs/2026-11-20__14-42-05`; proof: `proof/oracle-reward.json`).
