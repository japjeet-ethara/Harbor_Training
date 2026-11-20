# Akul Malviya — Harbor Training Day 4

[task/](task/) contains my titlecase task. The Day 4 practice version scored **1.0** with the Harbor oracle in job `day4-practice-oracle`.

I reviewed Yugal Lohani's task at the revision recorded in [TARGET.txt](attack/TARGET.txt). Three incomplete Go implementations ran in the local Harbor job `day4-functional-baselines`.

- **Capitalize word starts** scored **0.3390**, matching 517 of 2,000 hidden lines. [Reward JSON](attack/results/cheat1-reward.json)
- **Normalize word casing** scored **0.3557**, matching 567 of 2,000 hidden lines. [Reward JSON](attack/results/cheat2-reward.json)
- **Apply a small-word list** scored **0.3550**, matching 565 of 2,000 hidden lines. [Reward JSON](attack/results/cheat3-reward.json)

All three builds passed. The Python-removal check scored 0.0 in each trial because the baselines left the original Python files in place. The highest overall reward was **0.3557**.

The [Day 4 report](attack/ATTACK.md) includes the trial IDs, verifier findings, and proposed fixes.

The [Day 5 hardening report](HARDEN.md) documents the isolated verifier, the 100,000-title exam, and the before-and-after measurements for three Go ports.
