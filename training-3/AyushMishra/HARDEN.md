## Holes closed

- **Cheat 1** went from 1.00 to 0.05 ([hardened job](jobs/2026-11-20__13-02-45/result.json), [reward details](proof/cheat1/reward-details.json)). The verifier loads fixtures into memory and pipes the inputs to a static Go binary running in a fresh chroot as an unprivileged user. The jail contains only the binary, and the verifier compares stdout against the expected answers in memory.
- **Cheat 2** went from 1.00 to 0.05 ([hardened job](jobs/2026-11-20__13-06-18/result.json), [reward details](proof/cheat2/reward-details.json)). The jail contains no Python interpreter. The workspace check also rejects Python files, shebangs, ELF files, and the disallowed Go imports and process-launch markers.
- **Cheat 3** went from 0.3333 to 0.05 ([hardened job](jobs/2026-11-20__13-09-48/result.json), [reward details](proof/cheat3/reward-details.json)). Behaviour now accounts for 90% of the reward, and the workspace check earns its 5% only when behaviour scores at least 0.9. A buildable submission with no correct output earns only the 5% build credit.

The before scores come from the [original attack report](task/ATTACK.md).

## Exam: before and after

The old exam used 2,000 inputs. The new exam uses 100,000 inputs with answers generated using Python's standard-library `re` mode. The [answer-generation report](key/report.txt) records that the optional `regex` package was disabled.

All three Go implementations were compiled and run against the same 100,000 frozen inputs and reference answers.

| Port | Wrong on new exam | Accuracy | Old exam caught it? | Chance 2K random misses it |
|---|---:|---:|---|---:|
| My oracle ([final comparison](measure/my-oracle-iter3.txt)) | 0 / 100,000 | 100.000% | n/a | 100% |
| Madhur Jain | 857 / 100,000 | 99.143% | Unverified | 0% |
| Saurabh Baghel | 3,520 / 100,000 | 96.480% | Unverified | 0% |

The [latest Harbor oracle run](jobs/2026-11-20__13-44-46/result.json) scored **1.000** with zero exceptions.

The miss probabilities are rounded to whole percentages and assume a uniform sample of 2,000 cases drawn without replacement from the new exam. The two classmate comparisons cover the new exam only. A displayed 0% means the probability is extremely small, not mathematically impossible.

Madhur's port had mismatches involving words after underscores. For example, it changed `_via` to `_Via`, while the reference preserved `_via`.

Saurabh's port incorrectly capitalized version strings such as `v1.2`, changing them to `V1.2`, while the reference preserved the lowercase version string.

My Oracle produced zero mismatches across all 100,000 inputs. This demonstrates agreement with the frozen reference suite, although it does not prove correctness for every possible input.

## What I learned

I learned to keep expected answers in the verifier and give the submitted program only the input it needs.

I learned that compilation deserves little credit when a program produces no correct output.

I learned that a 2,000-case sample can miss all 40 failures about 45% of the time, as it could have for [my second oracle iteration](measure/my-oracle-iter2.txt).

I also learned that comparing implementations against the same large, frozen reference suite exposes subtle differences that smaller tests can easily miss.