# Day 6 — Proof and Defense

## 1. Proof results

Harbor 0.25.0 was run against the final Day 5 task. Each run completed with no Harbor exceptions. Direct verifier reward files and job references are in `proof/`.

| Candidate | Score | Job folder |
|---|---:|---|
| Original Go oracle | 1.0 | `jobs/ayush-day6-oracle` |
| Empty (`nop`) | 0.0 | `jobs/ayush-day6-nop` |
| Nitin cheat 1: read hidden expected file | 0.0 | `jobs/ayush-day6-cheat1` |
| Nitin cheat 2: partial titlecase rules | 0.0 | `jobs/ayush-day6-cheat2` |
| Nitin cheat 3: launch Python from Go | 0.0 | `jobs/ayush-day6-cheat3` |

The exact job IDs, trial IDs, and local job paths are recorded in `proof/JOBS.md`. Reward values are copied from each trial's `verifier/reward.json`.

## 2. What changed on Day 5

The original task let the candidate read expected answers and gave partial behavior credit. I moved to a protected answer file read by the verifier, ran the candidate as an unprivileged user, restricted candidate access to Python, and changed behavior scoring to require exact complete output. I also retained the old 2K regression set and added a frozen 100K test set using the `without-regex` reference mode.

## 3. Before and after exam comparison

| Go port | Old hidden 2K | New 100K | Error rate |
|---|---:|---:|---:|
| Ayush oracle | 0 wrong / 2,000 | 0 wrong / 100,000 | 0% |
| Aahan Trikha | 0 wrong / 2,000 | 3,900 wrong / 100,000 | 3.9% |
| Charitra | 0 wrong / 2,000 | 0 wrong / 100,000 | 0% |

These measurements are saved in `measure/my-oracle.txt`, `measure/AahanTrikha.txt`, and `measure/Charitra.txt`. The oracle and Charitra rows show that the 100K exam did not just reject every implementation; both passed. Aahan's 2K pass alongside 3,900 errors on the larger exam shows how edge cases can be missed by a small sample.

## 4. Five-minute talk outline

**0:00–1:00 — Strongest cheat.** Cheat 1 simply printed the hidden answer file and scored 0.6667 before hardening. The candidate and verifier shared access to that fixture, so the task rewarded data theft instead of the Go implementation.

**1:00–2:00 — The fix.** Answers are now stored for verifier use only. The candidate runs unprivileged and cannot access the root-owned answer file. Behavior requires exact complete output, while the Python check is reinforced at runtime by removing interpreter access.

**2:00–3:30 — Exam improvement.** I generated 100,000 unique inputs with seed 1, froze the no-regex reference twice, retained all 100,000 stable records, and preserved the old hidden 2,000 as regression cases. The Go oracle scored 1.0 on Harbor and had zero mismatches in the 100K comparison.

**3:30–4:30 — Before and after.** The three Nitin cheats moved from 0.6667, 0.0887, and 0.0887 to 0.0 each. The Day 6 `nop` scored 0.0, and the original oracle scored 1.0.

**4:30–5:00 — Surprise and limits.** Aahan's implementation passed the old 2K set but missed 3,900 cases in the 100K exam. That demonstrates the value of broader evaluation. The tests only establish resistance to these supplied attacks and inputs, not all possible future cheats.

## 5. Attacker rerun status

I reran all three supplied cheats myself on the final hardened task; all scored 0.0. The training instructions also ask Nitin to independently rerun them and append results to his `ATTACK.md`. That independent action is still pending; his folder has not been modified.

## 6. Remaining limitations

- The exam is finite, and untested inputs may expose additional behavior differences.
- These results cover the three supplied cheats, not arbitrary malicious native code or all sandbox escape methods.
- Independent attacker confirmation and the live five-minute presentation have not occurred yet.
