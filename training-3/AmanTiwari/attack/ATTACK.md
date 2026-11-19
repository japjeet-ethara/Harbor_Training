# Attack on Ayush Khurana's titlecase-go task

Target: `ayushkhurana/titlecase-go` in `japjeet-ethara/Harbor_Training`, commit
`3d26d51533b80ed2caf086fe4024246b8fa718f7` (see `TARGET.txt`).
All file:line references are to that commit. The copy Ayush later pushed to
`training-3/AyushKhurana/task/` (commit `9234582`) has the same 49 files byte for byte, plus one
new `.gitattributes` (line endings only), so every result below applies to it too.

## Reading the exam

1. **What the agent sees.** Only the original Python project: `environment/Dockerfile:9`
   (`COPY repo/ /workspace/repo/`). `tests/` and `solution/` are not in the agent image.
2. **What is scored.** Four checks (`tests/checks/common.py:59-91`), but only `behaviour` pays:
   `tests/checks/reward.toml:7` (`behaviour = 1.0`, the others `0.0`). `behaviour` is 0 unless
   no `.py` files remain, the no-exec rule passes and the program builds (`common.py:77-81`).
3. **Inputs.** `tests/data/hidden_inputs.txt` + `hidden_expected.txt` (2,000 lines), read in
   `common.py:82-84`. The visible `inputs.txt` / `expected.txt` share no lines with the hidden set.
4. **Is `tests/` visible while the agent works?** No. The verifier is a separate container
   (`task.toml:22`) and `/tests` is root-only (`tests/Dockerfile:13`). The agent's program
   runs as `nobody` (`common.py:86`).
5. **Three weakest points.**
   - `common.py:47`: the no-exec gate lists imports with `go list ./...`, which never
     enters a nested Go module. The text scan (`common.py:19`) bans only `StartProcess` and
     `go:linkname`. The image still has `/usr/bin/python3` (3.11.2), the same Python that made the answers.
   - `task.toml:32`: the agent room has `network_mode = "public"`, and the whole task,
     hidden answers included, is in a **public** GitHub repo.
   - `reward.toml:7` + `common.py:90`: the reward is the raw share of matching lines with no floor, so a
     weak port is paid for every line it happens to get right.

## Cheat 1 — Half port
What it does:   A real but tiny Go port of two rules only: capitalise every word, keep the NYT
                small words lower case except first/last. Nothing else (no Mc, acronyms, URLs, hyphens...).
Score:          reward 0.144  (build 1, no_python 1, no_exec 1, behaviour 0.144)
Job folder:     jobs/2026-11-18__17-46-41 (trial cheat1__rTQ9hPB)
Why it worked:  All gates pass honestly. Pay is the raw share of matching lines (`common.py:90`,
                `reward.toml:7`). The hidden set is weird enough that the easy rules get only a few lines right.
How to fix:     Nothing urgent: this part of the exam is strong. An optional floor
                (for example, pay 0 below 50% behaviour) would remove the leftover partial credit.

## Cheat 2 — Python inside, hidden in a nested Go module
What it does:   Keeps the original `titlecase/__init__.py` as `orig.txt`, embeds it, and runs it with
                `/usr/bin/python3`. `os/exec` lives in `./run`, which has its own `go.mod`
                and is wired in with `replace tc/run => ./run`. No real port at all.
Score:          reward 1.0  (build 1, no_python 1, no_exec 1, behaviour 1.0)
Job folder:     jobs/2026-11-18__17-48-33 (trial cheat2__3XCE7Lt)
Why it worked:  `common.py:47` runs `go list ... ./...` in the main module only, and `./...` skips nested
                modules, so the import list it checks is `fmt`, `embed`, `os`, `tc/run`, with no `os/exec`.
                `common.py:19` does not ban the text `os/exec`, and `.py` is only checked by extension (`common.py:42`).
                python3 is in the grader image (`tests/Dockerfile:3`, golang base), and `nobody` can run it.
How to fix:     Check imports with `go list -deps -f '{{.ImportPath}}' .` (all transitive deps of the built
                program) and reject the forbidden packages there, and/or reject any extra `go.mod`/`replace`.
                Better still, remove python3 from the grader image or run the program with an empty `PATH`
                and no `/usr/bin/python3*`.

## Cheat 3 — Download the hidden exam
What it does:   At solve time, `curl`s `hidden_inputs.txt` and `hidden_expected.txt` from the public
                class repo (pinned to commit 3d26d51), and ships a Go lookup table. Unknown lines are echoed back.
Score:          reward 1.0  (build 1, no_python 1, no_exec 1, behaviour 1.0)
Job folder:     jobs/2026-11-18__17-49-52 (trial cheat3__Hqv55NB)
Why it worked:  The agent has internet (`task.toml:32`, `network_mode = "public"`), and the hidden
                answers are published with the task. Hiding `tests/` inside the container does not
                help once the same files are on GitHub.
How to fix:     Give the agent no network (`network_mode = "no-network"`: nothing in this task needs it,
                since Go is stdlib-only and the image is pinned). Keep the canary GUID so leaked copies can be found.

**Highest score any cheat got: 1.0 (cheat 2 and cheat 3).**

All runs: `harbor run -p <copy of target with cheatN/solve.sh as solution/solve.sh> -a oracle`, Harbor on local Docker, 2026-11-18.
The reward files are in `results/cheatN-reward.json`, copied from each job's `verifier/reward.json`.
