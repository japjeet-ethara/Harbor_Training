## Cheat 1 — Lookup table

What it does: Loads input-output pairs from inputs.txt and expected.txt.\
Prints the stored answer on a match and Unknown otherwise.\
Score: reward 0.1667 (build 1, no_python 0, behaviour 0) [Saved reward](results/cheat1-reward.json)\
Job folder: jobs/2026-11-19__16-59-54\
Why it worked: The verifier build earned the entire reward. The exported workspace contained neither lookup fixture, and the behaviour score was zero. `target/tests/build.py:31` · `target/tests/reward.toml:4`\
How to fix: Keep answer fixtures isolated and require some correct output before awarding build credit.

## Cheat 2 — Partial port

What it does: Capitalizes the first letter of words and lowercases recognized interior small words.\
Omits special handling for acronyms, hyphens, and names.\
Score: reward 0.2777 (build 1, no_python 0, behaviour 0.1665) [Saved reward](results/cheat2-reward.json)\
Job folder: jobs/2026-11-19__17-15-24\
Why it worked: The grader awards behaviour credit per matching line. The partial port matched 333 of 2,000 hidden lines. `target/tests/behaviour.py:40`\
How to fix: Score coverage by rule so success on basic capitalization gives limited credit when special rules are missing.

## Cheat 3 — Empty Go program

What it does: Writes an empty Go main function and runs go build ./... [cheat3/solve.sh:9–15](cheat3/solve.sh#L9-L15).\
The launcher exited with status 1 when the default binary name collided with the bundled titlecase directory. The exported program has no stdin or stdout logic.\
Score: reward 0.1667 (build 1, no_python 0, behaviour 0) [Saved reward](results/cheat3-reward.json)\
Job folder: jobs/2026-11-19__17-25-24\
Why it worked: The verifier compiled the exported source using an explicit output path. The build criterion alone earned 0.1667. `target/tests/build.py:31` · `target/tests/reward.toml:4`\
How to fix: Require a nonzero behaviour score before awarding any overall credit.

**Highest score any cheat got: 0.2777 (Cheat 2).**
