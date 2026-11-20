# HARDEN.md

## Holes closed

Cheat 1 — Python inside: 1.0, now 0.1667 (job `jobs/2026-11-20__04-53-37`)

Fix: restricted Python in the verifier image and extended `no_python` to reject Go source that shells out to Python or uses executable/process APIs. The 100K exam also removes all visible answer overlap.

Cheat 2 — Lookup table: 0.5682, now 0.1765 (job `jobs/2026-11-20__04-57-52`)

Fix: replaced the 2,000-line overlapping pool with 100,000 frozen non-overlapping weird inputs and rejected lookup-table patterns in `no_python`.

Cheat 3 — Read the exam: 0.3337, now 0.1667 (job `jobs/2026-11-20__05-02-09`)

Fix: answer files are 0600, there is no visible/stale answer file, and `no_python` rejects filesystem answer-search patterns.

## Exam: before and after

Old exam: 2,000 inputs.

New exam: 100,000 inputs. Mode: **titlecase WITHOUT regex**. Frozen twice: 100,000 kept, 0 dropped.

| Port | Wrong on new exam | Old exam caught it? | Chance 2K random misses it |
|---|---:|---|---:|
| my oracle | 23 | n/a | 63% |
| SaurabhBaghel | 6,650 | unknown | 0% |
| Yuvraj-Singh | 4,027 | unknown | 0% |

Final Harbor oracle mean: 1.000. Final reward JSON: 0.9999.
