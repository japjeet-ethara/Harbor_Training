# HARDEN: titlecase-go (Ayush Khurana)

Attacker: Aman Tiwari. His report: `training-3/AmanTiwari/attack/ATTACK.md`, aimed at my task at commit `3d26d51533b80ed2caf086fe4024246b8fa718f7`.
Task folder after hardening: `training-3/AyushKhurana/task/`. Kit scripts: `kit/`. Exam record: `measure/`.

The task stays fair: an honest port that matches the original still scores 1.0. Nothing below cuts time, hides a requirement or changes what a correct answer is.

## Holes closed

| # | What Aman did (his numbers) | Why it worked | What I changed | Where |
|---|---|---|---|---|
| 1 | Half port: capitalise words, lowercase small words (0.144 on the old exam) | Behaviour pays by share of matching lines, so a weak port keeps partial credit | **Kept on purpose.** 0.144 is below the 0.2 line and a gradient is what makes the score useful. The exam it is measured on is now 100,000 lines plus a fresh 20,000, instead of 2,000, so the share is not luck. | `tests/data/`, `common.py` |
| 2 | Python hidden from the exec gate; his run scored 1.0 | `go list ./...` never enters a nested module, so `os/exec` lived in `./run` (`replace tc/run => ./run`). The gate banned only `StartProcess` and `go:linkname`, `.py` was checked by file name only, and `/usr/bin/python3` was still in the grader image | **(a)** The gate now reads the whole build: `go list -deps -json ./...`. Any nested `go.mod`, any `go.work`, any package outside the main module, `os/exec` anywhere in the dependency closure, `syscall` or `unsafe` in a module package, and any cgo, C or assembly file all make `no_exec` fail. **(b)** The grader image locks `/usr/bin/python3` and `/opt/uv` to root, so the agent's program (user `nobody`) cannot run Python even if a gate were beaten. **(c)** The program now runs with `PATH=/nonexistent`. | `tests/checks/common.py` `_no_exec`, `_packages`, `RUN_ENV`; `tests/Dockerfile` last `RUN` |
| 3 | Fetched the hidden answers from the public repo at solve time (1.0) | `[environment] network_mode = "public"`, and the answers were in a public repo | **(a)** The agent network is an allowlist (`api.anthropic.com`, `host.docker.internal`), so `raw.githubusercontent.com` is unreachable. **(b)** Even if the answers leak, the score is `min(frozen share, fresh share)`. The fresh exam is 20,000 new random lines made when grading starts (seed from `secrets`, answered by the original Python inside the grader), so no public file can contain it. | `task.toml` `[agent]`; `common.py` `behaviour_share`, `fresh_exam` |

Found by me while closing these (not in Aman's report): `net/http/cgi` pulls `os/exec` in through the standard library, and an assembly file can make system calls with no import. Both passed the old gate. Both fail the new one. Test scripts: `task/extra-cheat-tests/day5/gate_cgi.sh`, `gate_asm.sh`.

### Evidence (every number comes from a Harbor job folder)

Measured with `harbor run` as described in `task/extra-cheat-tests/RUN_DAY5.md`. The reward files are copied to `proof/`, and the allowlist probe (`proof/cheats-reward.txt`) showed `raw.githubusercontent.com BLOCKED`.

| Run | Expected | Reward | Job folder |
|---|---|---|---|
| oracle | 1.0 | 1 | `jobs/d5-oracle/` |
| nop | 0.0 | 0 | `jobs/d5-nop/` |
| Aman cheat 1 (half port) | below 0.2 | 0.1373 | `jobs/d5-aman1/` |
| Aman cheat 2 (hidden Python) | 0.0 | 0 | `jobs/d5-aman2/` |
| Aman cheat 3 (download answers) | 0.0, download blocked | 0 | `jobs/d5-aman3/` |
| lookup of all 100,000 answers + half port | below 0.2 | 0.1632 | `jobs/d5-hybrid/` |

## Exam: before and after

| | Before (Day 4) | After (Day 5) |
|---|---|---|
| Lines scored | 2,000 hidden (2,000 visible, not scored) | 100,000 fixed + 20,000 fresh at every grading |
| Where the answers come from | `tests/gen.py`, original Python in the task image | fixed set: `kit/make_pool.py` + `kit/answers.py`; fresh set: the same generator and the original Python 3.11 inside the grader |
| Public in the repo? | yes | the fixed set yes; the fresh set cannot be, it does not exist until grading |
| Score | share of hidden lines | the lower of the two shares |
| Mode | plain `re` | plain `re` (`regex` not installed); the freeze report says `regex module used False` |
| Unstable answers | not checked | each line is answered twice (`PYTHONHASHSEED` 1 and 2) and dropped if the answers differ; 100,000 of 100,000 were stable |
| Oracle against it | 1.0 | 0 wrong of 100,000 (`measure/oracle-100k.txt`) |

Freeze record: `kit/report.txt` (pool 100000, kept 100000, dropped 0, regex False). Pool seed 20261119.
Same answers come out under Python 3.11 and 3.12 (both without `regex`). With the optional `regex` package installed they change, so the fresh exam asserts `REGEX_AVAILABLE is False` and fails loudly instead of scoring against the wrong mode.

## What I learned

1. A gate must look at what is built, not at what a command happens to list. `./...` skips nested modules, so the check passed while the program did something else.
2. One lock is not enough. The static gate and the locked-down Python are separate layers, so beating one still does not give a cheat the original program.
3. A public answer key cannot be the only judge. Unseen lines generated at grading time make a lookup table worth almost nothing, and taking the lower of the two shares removes the reason to memorise.
4. "Same Python as the agent" is a real requirement. The grader's reference must be the image's own Python 3.11 in plain `re` mode, or the fresh exam would disagree with the frozen one.

## Limits I know about

- The allowlist depends on Docker's egress control. If a machine cannot do it, Harbor refuses the run instead of silently opening the network. The host list is my choice for model traffic; change it to what the agent really needs.
- A half port still earns about 0.14. That is deliberate (see hole 1).
- The fresh exam uses the same generator as the fixed one, so it tests the same kinds of lines. It stops memorising, not guessing rules.
