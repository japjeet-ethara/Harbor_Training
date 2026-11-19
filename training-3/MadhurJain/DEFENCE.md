# DEFENCE — Madhur Jain (notes for the 5-minute talk)

## 1. The strongest cheat against my task
Mukul Bhardwaj's partial Go port (cheat 3): 0.5056 before (jobs/mukul-cheat3-before), 0.1667 after (see proof/cheats-reward.txt).
Why it worked: my old grader paid behaviour as a plain share of titles right, and paid no_python for any program that built with no .py file left. A port that got only 26% of titles right still earned build, no_python and partial behaviour.
Fix: behaviour earns nothing below 90% right, then rises linearly to 1.0, and no_python pays only above 90% right. The partial port now earns only the build point.
Two holes Mukul did not try were also open in my old task: golang:1.23 ships python3, and the old verifier ran the program in the same container as the hidden answers in /tests/data. The port is now built static and run alone in an empty chroot as user nobody, which closes both.

## 2. My exam, before and after
Old: 2,000 hidden titles from my own word lists. New: 100,000 titles from the kit (seed 1), answers frozen twice (0 dropped), mode re (titlecase WITHOUT regex).
On the new exam my old oracle got 8,752 wrong, Satvik's port 50,750 and Mukul's port 8,752. My old exam caught only Satvik's. The full table is in HARDEN.md.

## 3. What surprised me
The new exam found a bug in my own oracle: words that start with "_" (_dream, __init__). Python's CAPFIRST is ^[PUNCT]*?(\w): lazy, and "_" is both punctuation and a word character, so the original leaves _dream alone. My port skipped every punctuation mark first and wrote _Dream. My old exam had no such word, so it gave me 1.0. One-line fix in capFirst: measure/my-oracle-before-fix.txt shows 8752 wrong, measure/my-oracle.txt shows 0.
A second surprise: Mukul's port, written independently, gives byte-identical output to my old oracle on all 100,000 titles. We made exactly the same mistake.

## What I could not close (honest limits)
- The program still has network access while it is graded, because the verifier needs it to install Reward Kit. Blocking the network inside the container needs privileges Docker does not give by default.
- The 90% floor means a port that is 89% right earns no behaviour points. I chose it because, on weird titles, an echo already gets about 5% right and a half port 14-25%, which would otherwise pass 0.2.
- The jail needs root and chroot in the verifier container. If that ever fails, behaviour is 0 for everyone, so the oracle proof would show it at once.

## Questions I expect
- Why a chroot, not just deleting python3? Python is also in uv's cache, and Reward Kit itself runs on Python. The jail removes everything at once: Python, /tests and /solution.
- Why user nobody? Root can climb out of a chroot; nobody cannot.
- Why mode re? My instruction already said WITHOUT regex, my port matched it, and the kit reported 0 unstable answers in this mode.
