## Holes closed

| Cheat | Before | After | Evidence | Fix |
|---|---:|---:|---|---|
| 1 - visible lookup | 0.18181818181818182 | 0.0 | `jobs/2026-11-20__17-29-03` | The cheat tried `/tests/data/expected.txt`, absent from the hardened suite; reward now comes only from behavior. |
| 2 - partial titlecase | 0.18181818181818182 | 0.07872 | `jobs/2026-11-20__17-30-08` | Grade against the frozen 100,000-title suite; partial behavior earns only its matching fraction. |
| 3 - build-only | 0.18181818181818182 | 0.0 | `jobs/2026-11-20__17-30-13` | Build and no-Python checks are prerequisites, not independently rewarded; exact output line count is required. |

The before scores and original job names are from Rucchika Kapoor's `attack/ATTACK.md`. All three re-attacks are below 0.2.

### Lookup follow-up

The original lookup cheat used the stale filename `/tests/data/expected.txt` and scored 0.0. A corrected version using `answers.txt` exposed that the verifier ran the submitted binary with access to the frozen answer files: it scored 1.0 in `jobs/2026-11-20__17-47-49`. The verifier now makes `/tests/data` root-only after Harbor uploads the tests and runs the submitted binary as uid/gid 65534. The corrected lookup then scored 0.0 with `permission denied` in `jobs/2026-11-20__17-56-15`.

## Exam: before and after

- Old exam: 2,000 inputs.
- New exam: 100,000 fixed-seed inputs; answers were frozen twice with the kit in `without regex` mode (`regex module used False`, 100,000 kept, 0 dropped).

| Port | Wrong on new exam | Old 2,000-input exam caught it? | Chance a random 2,000 misses all new failures |
|---|---:|---|---:|
| my oracle | 0 | n/a | 100% |
| AahanTrikha | 3,900 | no | 0% |
| RudranshPandey | 28,064 | no | 0% |

The oracle was compared against all 100,000 frozen answers and passes Harbor at 1.0 (`jobs/2026-11-20__17-57-39`). Its first Harbor run scored 0.87637; that exposed differences between the task's embedded Go source and the already measured port. Restoring those behaviors made the full suite pass. After the verifier access restriction, the `nop` baseline still scores 0.0 (`jobs/2026-11-20__17-59-38`).

## What I learned

- A buildable, Python-free program is not evidence that the program implements titlecasing.
- Exact output length and byte-for-byte behavior checks prevent a matching prefix from earning credit.
- A diverse 100,000-title exam found thousands of failures that the old 2,000-title exam missed.