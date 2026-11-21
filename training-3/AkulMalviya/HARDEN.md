# Day 5 — Harden the titlecase task

## Verifier changes

Ayush Ranjan reported three scores of **0.0**. His report also confirmed that the candidate could read the expected answers in the original verifier, so the zero reward did not establish isolation. [Day 4 review](https://github.com/japjeet-ethara/Harbor_Training/blob/01e8aa77c3148143e4d9de8731ea8c6bd315a4f4/training-3/AyushRanjan/attack/ATTACK.md)

1. **Build-only submission.** The verifier checks that the root builds as an executable, then requires exactly one LF-terminated output record per input. The reward depends on exact output matches. Ayush's empty Go program scored **0.0 before and after**. The local Harbor job `day5-build-only` recorded trials `practice__kznaRfE` and `hardened__rdXxfX9`. [Build and output checks](task/tests/checks/build.sh#L20-L24), [line count and scoring](task/tests/checks/behaviour.sh#L21-L39).
2. **Answer-file exposure.** Harbor transfers the submission to a separate verifier with networking disabled. The compiled entry point runs as UID/GID 65534 from a filesystem containing only the executable. Expected answers are kept outside that filesystem and used by the trusted grader. The Docker smoke check in `jobs/day5-verifier-smoke` passed using a benign program that verified its UID and root directory contents. The reviewer's original lookup score was **0.0**. Ayush independently measured 0.0 on the first published hardened revision. See the [revision-specific proof](proof/cheats-reward.txt). [Harbor configuration](task/task.toml#L1-L9), [execution boundary](task/tests/checks/behaviour.sh#L8-L19).
3. **Python delegation.** The verifier rejects Python source and non-standard Go dependencies. The runtime filesystem contains no interpreter or importable Python package. The same isolation smoke check verified the runtime contents. The reviewer's original wrapper score was **0.0**. Ayush independently measured 0.0 on the first published hardened revision. See the [revision-specific proof](proof/cheats-reward.txt). [Source checks](task/tests/checks/no_python.sh).

The verifier normalizes CRLF fixture records to LF before evaluation and compares output as text bytes, including numeric-looking titles such as `004`. The smoke check awarded **1.0** for two exact records from CRLF fixtures and **0.5** after changing one expected record from `004` to `4`. [Fixture normalization](task/tests/checks/behaviour.sh#L1-L7), [exact comparison](task/tests/checks/behaviour.sh#L28-L39).

## Exam and measurements

The old exam had 2,000 graded titles. The new exam has **100,000 unique titles** generated with seed **1**. Separate CPython 3.14.10 processes ran the vendored titlecase 2.4.1 reference in built-in `re` mode. Both agreed on every answer, so no generated title was dropped. [Generation report](kit/report.txt), [reference mode](task/instruction.md).

| Go port | Wrong on old exam | Wrong on new exam | Chance a random 2,000 from the new pool misses every error |
| --- | ---: | ---: | ---: |
| My corrected oracle | 0 / 2,000 | 0 / 100,000 | — |
| Ayush Ranjan | 151 / 2,000 | 17,442 / 100,000 | < 0.000001% |
| Yugal Lohani | 0 / 2,000 | 5,882 / 100,000 | < 0.000001% |

Each port was built with Go 1.23 in a Docker container with networking disabled. I extracted the Go source from the classmates' solution files at commit `01e8aa77c3148143e4d9de8731ea8c6bd315a4f4` and ran the resulting programs on identical fixtures. The old suite used the original committed hidden input and answer pair. These results measure compatibility with my two exams, including the stated `re` reference mode. [Oracle measurement](measure/my-oracle.txt), [Ayush measurement](measure/AyushRanjan.txt), [Yugal measurement](measure/YugalLohani.txt).

On the hardened task, Harbor scored the oracle **1.0** with all 100,000 lines matched in `day5-100k-oracle/task__D7KYSt8`. The no-op scored **0.0** in `day5-100k-nop/task__D2xZNSR`. Harbor logs are under the local ignored `jobs/` directory.

Run the following commands from the named submission folder to regenerate the exam:

```text
uv run --no-project --python 3.14.10 python -I -B kit/make_pool.py 100000 1 pool.txt
uv run --no-project --python 3.14.10 python -I -B kit/answers.py task/environment/python-titlecase pool.txt key
```

## What the larger exam caught

The original oracle passed the old 2,000 cases and missed **1,595** titles on the new exam. One rule detected internal capitals after punctuation where Python's pattern only checks the initial letter run, causing strings such as `X-RAY` to skip compound processing. Another rule reconsidered the period in a matched `v.` subphrase, while Python resumes after the entire match. Correcting both rules brought the mismatch count to **zero** without changing the generated cases. [Subphrase fix](task/solution/solve.sh#L328-L341), [internal-capital fix](task/solution/solve.sh#L468-L481).

## Day 6 scoring follow-up

Ayush's older Go port scored **0.82558** on the published verifier despite **17,442** wrong answers. The follow-up caps partial credit at **0.19**, while exact parity still scores **1.0**. The same older port matched the same **82,558** lines in the Harbor rerun and scored **0.19**. Fresh oracle, no-op, and build-only runs scored **1.0**, **0.0**, and **0.0** respectively. [Updated proof](proof/cheats-reward.txt)
