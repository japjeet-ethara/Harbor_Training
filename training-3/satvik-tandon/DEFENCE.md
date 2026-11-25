# Day 6 defence — Satvik Tandon

## Proof on my current task

The verifier grades 100,000 rebalanced titles in a shuffled order. Build,
standard-library-only, and no-Python checks are prerequisites; the reward is
the fraction of output lines matching the frozen answers exactly. The binary
runs as an unprivileged user in an empty `chroot`, without access to Python or
the answer files.

| Run | Reward | Harbor job |
| --- | ---: | --- |
| My oracle | **1.0** | `jobs/satvik-rebalanced-oracle` |
| Nop | **0.0** | `jobs/satvik-rebalanced-nop` |
| Madhur cheat 1: delete Python and echo | **0.01888** | `jobs/satvik-rebalanced-cheat1` |
| Madhur cheat 2: run embedded Python | **0.0** | `jobs/satvik-rebalanced-cheat2` |
| Madhur cheat 3: read hidden answers | **0.01888** | `jobs/satvik-rebalanced-cheat3` |
| Madhur's new Day 6 cheat 4: partial Go port | **0.11065** | `jobs/satvik-rebalanced-cheat4` |

The oracle and nop meet the required scores, and all four cheats are
below 0.2 on this exam. Cheat 4 previously scored 0.21175 on the first
100,000-title exam (`jobs/satvik-stdlib-shuffle-cheat4-current`). The required proof
files are in `proof/`; Madhur's original and re-attack results are in
[`../MadhurJain/attack/ATTACK.md`](../MadhurJain/attack/ATTACK.md).

## Strongest cheat and what changed

Madhur's original Python-wrapper and answer-reading cheats each scored **1.0**
against my Day 4 task. Running the built Go binary in an empty `chroot` closed
both paths: their current rewards are **0.0** and **0.01888**, respectively.
Build and deleting Python files no longer award points by themselves, so the
echo cheat earns **0.01888** instead of **0.33533**. The before and after jobs
are listed in [`HARDEN.md`](HARDEN.md).

The new cheat 4 is a short Go program that applies only a few titlecase rules:
it capitalizes word starts, handles a small-word list, and preserves all-caps
words. It does not use Python, read the answer file, or break the build rules.
It matched 21,175 lines on the first 100,000-title exam. I rebalanced the
existing generator toward compound words, apostrophes, punctuation, and Unicode
cases. On the new 100,000-title exam it matches **11,065** complete lines,
giving **0.11065**. This is still exact matches divided by 100,000; I did not
add a 90% scoring floor.

## Before and after exam

The old hidden exam had 2,000 titles. The rebalanced exam has 100,000 distinct
titles generated from seed 1, with answers from the original Python 3.14 titlecase in
plain `re` mode. The answer generator ran the original twice and kept all
100,000 stable results; see [`kit/report.txt`](kit/report.txt).

| Go port | Wrong on old 2,000 | Wrong on new 100,000 |
| --- | ---: | ---: |
| My original oracle | 0 | 41,859 |
| My hardened oracle | 0 | 0 |
| Priya Kumari's port | 0 | 765 |
| Neha Gaur's port | 0 | 4,349 |

The measurements and representative mismatches are in [`measure/`](measure/).
The surprise was that my original oracle passed every old title while missing
41,859 in the rebalanced exam. I fixed its whitespace, punctuation, acronym,
apostrophe, and Unicode handling rather than removing any failing cases.

## Later verifier review and remaining limit

Comparing classmates' verifiers exposed an unenforced rule: disabling Go module
downloads did not reject a local third-party dependency. The verifier now
checks the complete imported package list. A replaced-module test scored
**0.0** in `jobs/satvik-stdlib-shuffle-vendored`. Shuffling the same 100,000
input/answer pairs also dropped a fixed-order answer replay to **0.00001** in
`jobs/satvik-stdlib-shuffle-replay`.

These checks do not make a partial Go port wrong on titles it handles. The
rebalanced exam lowers cheat 4 through broader titlecase cases while preserving
the direct score. A lookup table keyed by the public input titles could still
survive shuffling; unseen cases would be needed to close that separate limit.
