# Day 6 — Five-minute defence

Ayush tested published revision `2fbaa10`. The follow-up scoring fix is in local revision `9b57ca6`. [Day 5 report](HARDEN.md)

## 0:00–1:15 | The strongest finding

All three of Ayush's original submissions recorded **0.0**. The answer-file lookup exposed the most serious flaw: the candidate could read the grader's answers. Ayush reported that different fixture and output line endings masked the exposure. The lookup also scored **0.0** after hardening. This time, the verifier kept the answers outside the candidate's filesystem. [Ayush's rerun](https://github.com/japjeet-ethara/Harbor_Training/blob/6a22cbfad12f118447ced7f48614ea6359f84958/training-3/AyushRanjan/attack/ATTACK.md#day-6--rerun-against-akuls-hardened-task)

## 1:15–2:30 | What I changed

I moved grading to a separate verifier and confined the candidate process to an unprivileged runtime with only its compiled executable. The process receives titles on stdin. The trusted grader retains the expected answers outside that runtime. I also normalized fixture line endings and made the grader check the output record count, final newline, and exact content. The separate runtime has no Python interpreter. [Verifier configuration](task/task.toml), [grader](task/tests/test.sh).

## 2:30–3:30 | Before and after

I expanded the exam from **2,000** to **100,000** unique titles using seed 1. Two isolated Python reference processes agreed on every expected answer in built-in `re` mode. The following counts show wrong answers on the same fixtures for all three ports.

| Port | Old exam | New exam |
| --- | ---: | ---: |
| My corrected oracle | 0 / 2,000 | 0 / 100,000 |
| Ayush Ranjan | 151 / 2,000 | 17,442 / 100,000 |
| Yugal Lohani | 0 / 2,000 | 5,882 / 100,000 |

## 3:30–4:15 | What surprised me

My original oracle had a perfect score on 2,000 titles and still missed **1,595** on the larger exam. For `X-RAY`, my Go port looked for internal capitals past the hyphen and skipped the compound rule. It also reconsidered the period in a matched `v.` subphrase, where Python resumes after the entire match. I fixed those rules and kept all 100,000 cases.

## 4:15–5:00 | What the evidence proves

- Harbor verified **1.0** for the corrected oracle, with all 100,000 lines matched. [Oracle evidence](proof/oracle-reward.json)
- Harbor verified **0.0** for the no-op. Ayush independently reran the three original shortcuts on the published revision. All three scored **0.0** and met the strict `< 0.2` cutoff. [No-op evidence](proof/nop-reward.json), [reviewer reruns](proof/cheats-reward.txt)
- Ayush's extra heuristic scored **0.06136**. His older Go port scored **0.82558** because it matched 82,558 of 100,000 titles, leaving 17,442 errors. I kept exact parity at **1.0** and capped every incomplete result at **0.19**. The cap preserves the grader's ability to distinguish low partial scores. [Additional probe evidence](https://github.com/japjeet-ethara/Harbor_Training/blob/6a22cbfad12f118447ced7f48614ea6359f84958/training-3/AyushRanjan/attack/results/AKUL-HARDENED-RERUN.md), [scoring rule](task/tests/test.sh#L74-L84).
- With the fix, the older Go port still matched 82,558 titles and now scored **0.19**. Fresh Harbor controls confirmed that the oracle still scored **1.0** and both the no-op and build-only program scored **0.0**. [Follow-up Harbor evidence](proof/cheats-reward.txt)
