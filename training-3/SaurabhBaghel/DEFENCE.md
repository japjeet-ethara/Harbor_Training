# Day 6: Prove It and Defend It

## Evaluation and source limitations

Every score below was produced by the task's `tests/test.sh` and Reward Kit in a network-disabled Docker container. The genuine reward outputs are retained under [proof/](./proof/).

The attacker folder has no supporting source files for cheats 1 and 2, and the job folders named in the attack report are not present. Those two submissions were reconstructed in disposable workspaces from the documented strategies; their scores are real verifier results for those reconstructions, not results from the missing original job artifacts. Cheat 3 used the current on-disk script body after removing only the malformed text before its shebang. No attacker files, including `ATTACK.md`, were changed.

## Vulnerabilities and fixes

1. **Build-only and partial-credit reward.** With the old weights, a submission that built and passed the Python check could earn `0.3333` despite producing no correct behavior. Behavioral grading is now all-or-nothing over the complete output bytes, with behavior weighted 100 against build and no-Python weights of 1 each. A non-behaving submission that passes both other checks can now earn at most `2/102 = 0.0196`.
2. **Python disguised by its file extension.** The previous check rejected `.py` files only. The strengthened check also parses other text files for import-bearing Python source with definitions or dynamic execution; the behavior runner independently executes only the compiled binary in a chroot.
3. **Small or visible-only exams.** A visible-fixture lookup and a basic capitalization implementation could exploit the former partial behavior score and 2,000-line exam. The expanded 100,000-line `regex`-mode exam covers additional punctuation, Unicode, contractions, and casing families. The exact-byte comparison rejects any incorrect, missing, extra, or line-ending-different output.
4. **Windows line-ending drift in the frozen exam.** Day 6 initially exposed CRLF bytes in the expanded input/answer copies, while the task requires LF output and exact byte comparison. The expanded exam artifacts were normalized to LF; their hashes now match the recorded freeze hashes. The kit writers/readers were made explicit about LF output and newline-independent input parsing. The oracle then scored 1.0.

## Fresh Day 6 results

| Submission | Build | No Python | Behavior | Reward | Evidence |
| --- | ---: | ---: | ---: | ---: | --- |
| Oracle | 1.0 | 1.0 | 1.0 | **1.0** | [reward](./proof/oracle/reward.json), [details](./proof/oracle/reward-details.json) |
| NOP | 0.0 | 0.0 | 0.0 | **0.0** | [reward](./proof/nop/reward.json), [details](./proof/nop/reward-details.json) |
| Cheat 1: visible-fixture lookup (reconstruction) | 1.0 | 1.0 | 0.0 | **0.0196** | [reward](./proof/cheat1/reward.json), [details](./proof/cheat1/reward-details.json) |
| Cheat 2: renamed Python implementation (reconstruction) | 1.0 | 0.0 | 0.0 | **0.0098** | [reward](./proof/cheat2/reward.json), [details](./proof/cheat2/reward-details.json) |
| Cheat 3: basic capitalization | 1.0 | 1.0 | 0.0 | **0.0196** | [reward](./proof/cheat3/reward.json), [details](./proof/cheat3/reward-details.json) |

All three tested cheat strategies score below 0.2. The result files contain the Reward Kit outputs; the exact exam and grading weights are documented in [instruction.md](./task/instruction.md) and [reward.toml](./task/tests/reward.toml).

## Before/after comparison

The old exam had 2,000 cases; the expanded exam has 100,000 cases and was independently frozen twice in `regex` mode. Port results are from [measure/README.md](./measure/README.md).

| Port | Old exam errors | Expanded exam errors |
| --- | ---: | ---: |
| SaurabhBaghel | 0 / 2,000 | 0 / 100,000 |
| Gaurav | 54 / 2,000 (2.7%) | 10,503 / 100,000 (10.503%) |
| SakshiSingh | 60 / 2,000 (3.0%) | 10,488 / 100,000 (10.488%) |

| Cheat | Before hardening | Day 6 verifier |
| --- | ---: | ---: |
| Cheat 1 | 0.3333 | 0.0196 |
| Cheat 2 | 0.3333 | 0.0098 |
| Cheat 3 | 0.579 | 0.0196 |

The pre-hardening values are the reported old-exam results in the attack report and its saved reward files. The Day 6 values above are fresh runs; for cheats 1 and 2 they apply to the documented reconstructions described above.

## Five-minute presentation outline

- **0:00–1:00 — Threat and strongest cheat:** Cheat 3 was strongest before hardening at 0.579 because ordinary titles earned partial credit.
- **1:00–2:00 — What changed:** Explain the all-or-nothing exact-byte behavior check, higher behavior weight, Python-source detection, and the larger exam.
- **2:00–3:30 — Before/after evidence:** Show the two tables above and the genuine reward files.
- **3:30–4:30 — One surprise:** The correct oracle initially failed exact-byte grading because the Windows exam copy used CRLF. Normalizing the exam to the required LF made the same oracle pass at 1.0.
- **4:30–5:00 — Close:** State the final result: Oracle 1.0, NOP 0.0, and every tested cheat below 0.2; disclose the missing original support artifacts for cheats 1 and 2.
