# Day 5 titlecase grader hardening

I reran the three submitted scripts against the Day 4 task snapshot (`3801b4d`). All three baseline rewards matched Tannu Kumari’s report. The third script prints the old visible answer file in its original order, so the table describes that submitted script. [Reviewer’s report](../TannuKumari/attack/ATTACK.md)

## Holes closed

| Submitted shortcut | Before | After | Fix |
| --- | --- | --- | --- |
| 1. Read the verifier’s hidden answers | 1.0000 (`before-cheat1/before-cheat1__iypXwQx`) | 0.0000 (`verified-final-cheat1/final-cheat1__QoPFYuL`) | The Go binary runs as an unprivileged user in a temporary root that contains only the compiled executable. The original answer file stays outside that root. |
| 2. Read the same file and leave Python source behind | 0.8333 (`before-cheat2/before-cheat2__kmDpdwj`) | 0.0000 (`verified-final-cheat2/final-cheat2__mj3XZmw`) | The filesystem restriction also applies to this submission. The Python-source check rejects it before execution. |
| 3. Replay the old visible answers | 0.3333 (`before-cheat3/before-cheat3__2jjkiKN`) | 0.0000 (`verified-final-cheat3/final-cheat3__SDNmdfZ`) | The build and Python-source checks are prerequisites. All credit comes from exact output, including fresh cases generated for each run. |

The verifier runs offline and compares outputs outside the submitted process. It writes the reward directly to Harbor’s JSON file, preserving the exact match fraction so a score of 0.99999 stays below 1.0. The oracle scored 1.0 in `verified-oracle/task__wbiYnJX` with exact matches on the original, frozen, and fresh sets.

## Exam before and after

The old hidden exam has 2,000 cases and remains in the verifier as a regression set. The new frozen exam has 100,000 unique inputs generated with seed 1, including dotted numbers, `Mcx-`, combining marks, and additional Unicode spaces. Two Python 3.14 runs of python-titlecase 2.4.1 in standard-library `re` mode agreed on all 100,000 answers. The verifier also generates 2,000 fresh titles per trial by combining sampled inputs with random lowercase words. [Freeze report](kit/report.txt)

| Port | Wrong on old exam | Wrong on new exam | Old exam caught it? | Chance a random 2,000 from the new exam misses every error | Harbor job and trial |
| --- | ---: | ---: | --- | ---: | --- |
| Uday Bhatnagar’s oracle | 0 / 2,000 | 0 / 100,000 | No errors | — | `verified-oracle/task__wbiYnJX` |
| Tannu Kumari | 8 / 2,000 | 3,321 / 100,000 | Yes | 0% rounded | `day5-port-TannuKumari/measure-TannuKumari__6kyoxcH` |
| Madhur Jain | 0 / 2,000 | 0 / 100,000 | No errors | — | `day5-port-MadhurJain/measure-MadhurJain__kVZ8aba` |

The port sources come from checkout `e5c9367`. Both exam counts matched in Harbor and offline Docker, where I ran the same Go ports and compared their output with `kit/compare.py`. The Harbor jobs and their reward files are in the local Day 5 jobs directory. [Oracle measurement](measure/my-oracle.txt) · [Tannu’s measurement](measure/TannuKumari.txt) · [Madhur’s measurement](measure/MadhurJain.txt)

## What I learned

- A verifier can hide its files during the agent phase and still expose them if it runs the submitted executable in the same filesystem.
- Build and cleanup checks matter as prerequisites. Giving them standalone credit let a replay earn one-third of the reward.
- The suites caught different cases in Tannu’s port. The old exam exposed the `ﬁ` ligature, and the new one repeatedly exposed uppercase expansion of `ß` after an apostrophe.
