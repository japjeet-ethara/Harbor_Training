# Attack on Satvik Tandon's titlecase-go task

Target: Satvik Tandon, commit 5c4ffcac9129949f2a72d60fa214129b6bf3a0d7 (TARGET.txt). Each cheat ran as the oracle in a scratch copy of his task, with only solution/solve.sh replaced.

## Cheat 1 — Delete trick
What it does:   Deletes every .py file and replaces the program with a Go program that prints each input line unchanged.
                It contains no titlecase logic at all.
Score:          reward 0.335  (build 1, no_python 1, behaviour 0.003)
Job folder:     jobs/satvik-cheat1/satvik-cheat1__22gfRHe
Why it worked:  tests/verify.py:10 pays no_python as soon as the build passes and no *.py file is left. It never checks
                that any answer is right, so deleting files alone is worth 1/6 on top of the 1/6 for building.
How to fix:     Pay no_python only when the program also gets real answers right (for example, at least one hidden
                title that it had to change).

## Cheat 2 — Python inside
What it does:   Renames the original titlecase/__init__.py to pysrc/titlecase.txt, embeds it in a Go program, and at
                run time feeds every line to the original Python code through python3.
Score:          reward 1.0  (build 1, no_python 1, behaviour 1.0)
Job folder:     jobs/satvik-cheat2/satvik-cheat2__NZzUU32
Why it worked:  tests/Dockerfile:3 installs python3 in the image where the program is graded, and tests/verify.py:10
                only looks for files ending in .py, so Python code under another name passes the check.
How to fix:     Grade in an image without Python, or run the built binary inside an empty chroot that contains
                nothing but the binary, so python3 cannot be found.

## Cheat 3 — Read the exam
What it does:   At run time reads /tests/data/hidden_inputs.txt and hidden_expected.txt and prints the stored answer
                for each input line. It contains no titlecase logic.
Score:          reward 1.0  (build 1, no_python 1, behaviour 1.0)
Job folder:     jobs/satvik-cheat3/satvik-cheat3__xLG3jyy
Why it worked:  tests/verify.py:13 runs `go run .` inside the verifier container, and tests/Dockerfile:7 copied the
                hidden answers into that same container at /tests/data, where the program under test can read them.
How to fix:     Read the answers into the grader's memory first, then run the binary where /tests does not exist
                (an empty chroot, or a user with no access to /tests).

## Another weak point (not run as a cheat)
Visible and hidden titles are built from the same list of about 50 words (tests/gen.py:13-16, 42-43), so a word-by-word
lookup learned from the visible files would get most hidden titles right. Fix: a bigger and weirder pool of inputs.

**Highest score any cheat got: 1.0 (cheat 2 and cheat 3).**

## Day 6 re-attack (Satvik's hardened task, commit 5b700823ffb4a3bfad3fea2849c9cf83d1b3e3d3)
His fixes: the program is built static and run as user nobody in an empty chroot; build and no_python are now prerequisites, and reward = behaviour (tests/verify.py:63-85). The exam is now 100,000 titles.

Cheat 1 (Delete trick / echo): reward 0.01371   job folder: jobs/satvik-recheat1/satvik-re1__gtxRQU7
                Closed: build and no_python no longer pay on their own; an echo only matches the 1,371 titles that need no change.
Cheat 2 (Python inside): reward 0.0   job folder: jobs/satvik-recheat2/satvik-re2__BCNQXpG
                Closed: python3 cannot be reached inside the chroot, so the program fails and earns nothing.
Cheat 3 (Read the exam): reward 0.01371   job folder: jobs/satvik-recheat3/satvik-re3__CUaaazG
                Closed: the answer files stay outside the chroot, so the program can only echo.

## New cheat (Day 6): Cheat 4 - Rule-of-thumb casing (half port)
What it does:   No port. A short Go program that capitalises the first letter of every word, lowercases 21 small words
                (a, an, the, of, ...) unless they are first or last, and keeps ALL-CAPS words as they are.
Score:          reward 0.21175  (build 1, no_python 1, behaviour 0.21175)
Job folder:     jobs/satvik-recheat4/satvik-re4__yMCsZgg
Why it worked:  tests/verify.py:84-85 sets the reward to the plain share of titles right, with no floor. A crude rule that
                ports none of titlecase's logic still gets 21% of the 100,000 titles right.
How to fix:     Pay behaviour only above a high floor, for example nothing below 90% right, then linear to 1.0 at 100%.

**Highest score after his fixes: 0.21175 (cheat 4).**
