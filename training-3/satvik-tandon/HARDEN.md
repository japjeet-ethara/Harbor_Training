# Day 5 hardening report

The verifier now awards credit for correct output after the Go build and Python-source checks pass. It runs the statically linked program as UID 65534 in a temporary root containing only its executable. The trusted verifier keeps the answer key outside that root and sends the program the titles on stdin. Harbor disables network access for the verifier.

## Findings from Madhur Jain's review

| Submission from the review | Original Harbor reward | Hardened result |
| --- | ---: | --- |
| Echo after deleting Python sources | 0.33533 in `jobs/satvik-day5-echo-original-lf` | 0.01371 in `jobs/satvik-day5-madhur-exact-1` |
| Go wrapper around Python | 1.0 in `jobs/satvik-cheat2/satvik-cheat2__NZzUU32` | 0.0 in `jobs/satvik-day5-madhur-exact-2`. The isolated process cannot access Python. |
| Read the hidden answer key | 1.0 in `jobs/satvik-cheat3/satvik-cheat3__xLG3jyy` | 0.01371 in `jobs/satvik-day5-madhur-exact-3`. The isolated process cannot see the answer files. |

The hardened results use Madhur's original three scripts. Build and source removal each used to confer one sixth of the reward. They are now prerequisites, so the echo only earns credit for the 1,371 new titles that are already in the expected form. The verifier also rejects runs with the wrong number of output lines.

See [Madhur's original report](https://github.com/japjeet-ethara/Harbor_Training/blob/ae96885bdbcab8a6726074e08e2acfc80842d60f/training-3/MadhurJain/attack/ATTACK.md) and the implementation in [tests/verify.py](task/tests/verify.py).

## Exam comparison

The original hidden exam contained 2,000 titles. The kit generated 100,000 distinct titles with seed 1 and froze answers from the bundled Python reference in standard-library `re` mode on Python 3.14.10. Both reference runs agreed on all 100,000 answers. The child runs use different Python hash seeds and UTF-8 output on Windows. See [kit/report.txt](kit/report.txt).

| Go port | Wrong on the old exam (2,000) | Wrong on the new exam (100,000) | Chance a random 2,000 from the new exam misses all errors |
| --- | ---: | ---: | ---: |
| Satvik's original oracle | 0 | 39,344 | <1% |
| Satvik's hardened oracle | 0 | 0 | — |
| Priya Kumari | 0 | 857 | <1% |
| Neha Gaur | 0 | 3,520 | <1% |

I built the ports with Go 1.23 in Docker with networking disabled. The peer solutions came from class branch commit `ae96885bdbcab8a6726074e08e2acfc80842d60f`. Results and representative mismatches are in [measure/](measure/). The old corpus remains available in the published Day 4 commit `74c5b13`.

## Harbor checks

- Oracle earned **1.0** in `jobs/satvik-day5-verified-oracle`.
- Nop earned **0.0** in `jobs/satvik-day5-nop`.

The larger exam surfaced 39,344 disagreements in my original port after it passed the original 2,000 titles. I updated the Go port to preserve Python's whitespace handling, use the same punctuation and word boundaries, and match the reference's casing rules for acronyms, apostrophes, and Unicode. No fixtures were removed from the new corpus.
