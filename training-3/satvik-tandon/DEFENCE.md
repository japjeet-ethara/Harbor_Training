# Day 6 defence — Satvik Tandon

## Proof on my current task

The verifier grades the original 100,000 titles in a shuffled order. Build,
standard-library-only, and no-Python checks are prerequisites; the reward is
the fraction of output lines matching the frozen answers exactly. The binary
runs as an unprivileged user in an empty `chroot`, without access to Python or
the answer files.

| Run | Reward | Harbor job |
| --- | ---: | --- |
| My oracle | **1.0** | `jobs/satvik-stdlib-shuffle-oracle` |
| Nop | **0.0** | `jobs/satvik-stdlib-shuffle-nop` |
| Madhur cheat 1: delete Python and echo | **0.01371** | `jobs/satvik-final-cheat1` |
| Madhur cheat 2: run embedded Python | **0.0** | `jobs/satvik-final-cheat2` |
| Madhur cheat 3: read hidden answers | **0.01371** | `jobs/satvik-final-cheat3` |
| Madhur's new Day 6 cheat 4: partial Go port | **0.21175** | `jobs/satvik-stdlib-shuffle-cheat4-current` |

The oracle and nop meet the required scores, and all three original cheats are
below 0.2. Cheat 4 is a new finding and remains above 0.2. The required proof
files are in `proof/`; Madhur's original and re-attack results are in
[`../MadhurJain/attack/ATTACK.md`](../MadhurJain/attack/ATTACK.md).

## Strongest cheat and what changed

Madhur's original Python-wrapper and answer-reading cheats each scored **1.0**
against my Day 4 task. Running the built Go binary in an empty `chroot` closed
both paths: their current rewards are **0.0** and **0.01371**, respectively.
Build and deleting Python files no longer award points by themselves, so the
echo cheat earns **0.01371** instead of **0.33533**. The before and after jobs
are listed in [`HARDEN.md`](HARDEN.md).

The new cheat 4 is a short Go program that applies only a few titlecase rules:
it capitalizes word starts, handles a small-word list, and preserves all-caps
words. It does not use Python, read the answer file, or break the build rules.
Its **0.21175** reward means 21,175 of 100,000 complete output lines match.
Shuffling the same titles leaves this input-dependent score unchanged. A 90%
scoring floor would lower its reward without finding any more wrong answers, so
I did not add one.

## Before and after exam

The old hidden exam had 2,000 titles. The new exam has 100,000 distinct titles
generated from seed 1, with answers from the original Python 3.14 titlecase in
plain `re` mode. The answer generator ran the original twice and kept all
100,000 stable results; see [`kit/report.txt`](kit/report.txt).

| Go port | Wrong on old 2,000 | Wrong on new 100,000 |
| --- | ---: | ---: |
| My original oracle | 0 | 39,344 |
| My hardened oracle | 0 | 0 |
| Priya Kumari's port | 0 | 857 |
| Neha Gaur's port | 0 | 3,520 |

The measurements and representative mismatches are in [`measure/`](measure/).
The surprise was that my original oracle passed every old title while missing
39,344 in the larger exam. I fixed its whitespace, punctuation, acronym,
apostrophe, and Unicode handling rather than removing any failing cases.

## Later verifier review and remaining limit

Comparing classmates' verifiers exposed an unenforced rule: disabling Go module
downloads did not reject a local third-party dependency. The verifier now
checks the complete imported package list. A replaced-module test scored
**0.0** in `jobs/satvik-stdlib-shuffle-vendored`. Shuffling the same 100,000
input/answer pairs also dropped a fixed-order answer replay to **0.00001** in
`jobs/satvik-stdlib-shuffle-replay`.

These checks do not make a partial Go port wrong on titles it handles. They
also do not stop a lookup table keyed by the public input titles. Those limits
would require changing the exam inputs or using unseen cases. The new Day 6
cheat's **0.21175** is therefore reported as an open finding.
