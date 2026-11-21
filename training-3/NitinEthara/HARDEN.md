# Day 5 — Hardening `titlecase-go`

## Scope

The original task at `NitinEthara/titlecase-go/` and the attacker's files were left
unchanged. All changes are in the Day 5 copy at `training-3/NitinEthara/task/`.

## Attack reruns

Each before and after score is from a Harbor run. Before scores use the original 2,000-case
task; after scores use the hardened task and its 100,000-case exam.

| Attack | Before reward | After reward | After behavior | After job |
| --- | ---: | ---: | ---: | --- |
| Cheat 1 — echo input | 0.3347 | 0.0096 | 0.0144 | `jobs/cheat1-after/` |
| Cheat 2 — basic `strings.Fields` titlecasing | 0.5030 | 0.0606 | 0.0909 | `jobs/cheat2-after/` |
| Cheat 3 — partial capitalization rules | 0.5357 | 0.0979 | 0.1468 | `jobs/cheat3-after/` |
| Cheat 4 — complete Go port | 1.0000 | 1.0000 | 1.0000 | `jobs/cheat4-after/` |

The first three attacks now score below 0.2. The build and no-Python checks award credit
only when the program exactly passes the complete frozen exam; this removes the former
structural reward floor. The behavior check remains proportional to the number of exact
answers.

Cheat 4 is a valid, complete Go implementation of the requested behavior, not a bypass.
It correctly passes the larger exam, so it should keep full credit. Rejecting it would
require penalizing a correct solution rather than closing an exam weakness.

The post-hardening oracle scored 1.0 and the no-op scored 0.0. Reward and detail JSON files
for these checks and all four attacks are saved in `measure/attacker-reruns/`. Full job
outputs are local-only under `jobs/`.

## Exam and port measurements

The old exam had 2,000 inputs. The replacement exam has 100,000 stable inputs generated
with seed 1 in `regex` mode; no unstable cases were dropped. The mode and supported input
contract are documented in `task/instruction.md`. Frozen inputs and answers are in
`task/tests/data/`.

| Port | Wrong on old exam | Wrong on new exam | Old exam caught it? | Chance a random 2K exam misses all errors |
| --- | ---: | ---: | --- | ---: |
| Nitin oracle | 0 / 2,000 | 0 / 100,000 | No errors | 100% |
| Adarsh Sahani complete Go port | 0 / 2,000 | 0 / 100,000 | No errors | 100% |
| Ayush Ranjan Go port | 47 / 2,000 | 10,833 / 100,000 | Yes | 0% |

The comparisons are recorded in `measure/my-oracle.txt`, `measure/AdarshSahani.txt`, and
`measure/AyushRanjan.txt`.

## What I learned

- Structural checks must depend on real behavior, or a compiling placeholder earns reward.
- A larger, broader exam exposed many mismatches in a port that had relatively few errors on
  the old exam.
- A strong exam should reject shortcuts while continuing to reward a correct full port.
