# Attack on Kushal Soni's task

- **Target:** `training-3/KushalSoni/task/` at commit `42e9bfe` (full SHA in `TARGET.txt`).
- **How every cheat was run:** on a local copy of the task with only `solution/solve.sh` replaced
  (checked with `diff -rq`: no other file differs), using Harbor 0.26.0:
  `harbor run -p <copy> --env docker -a oracle`. Job folders are kept locally (not pushed).
- **Score formula** (`tests/reward.toml:4`): reward = (build + no_python + 4 × behaviour) / 6.

| Cheat | Reward | build | no_python | behaviour | Job folder |
|---|---|---|---|---|---|
| 1 — Build trick | **0.3333** | 1 | 1 | 0 | `jobs/2026-11-23__12-07-58` |
| 2 — Python inside | **1.0** | 1 | 1 | 1.0 | `jobs/2026-11-23__12-15-23` |
| 3 — Half port | **0.9997** | 1 | 1 | 0.9995 | `jobs/2026-11-23__12-16-17` |

## Cheat 1 — Build trick

```
What it does:   Deletes the .py files and writes an empty Go program (func main() {}).
                It compiles, reads nothing and prints nothing.
Score:          reward 0.3333  (build 1, no_python 1, behaviour 0)
Job folder:     jobs/2026-11-23__12-07-58
Why it worked:  tests/reward.toml:4 gives build and no_python 2 of the 6 weight points.
                tests/build.py:38-41 and tests/no_python.py:30-36 pay them whenever the
                repo compiles, no matter what the program prints.
                (behaviour.py:50-54 correctly gave 0: that part is strong.)
How to fix:     Pay build and no_python only when behaviour is already high (for example
                behaviour >= 0.5), or make them pass/fail gates that set the whole reward
                to 0, instead of points that add up on their own.
```

## Cheat 2 — Python inside

```
What it does:   Copies the original titlecase/__init__.py to titlecase_src.txt, deletes
                every .py file, and writes a Go wrapper that embeds that text (go:embed)
                and runs it with `python3` at run time. No titlecase logic is in Go.
Score:          reward 1.0  (build 1, no_python 1, behaviour 1.0)
Job folder:     jobs/2026-11-23__12-15-23
Why it worked:  tests/no_python.py:34 only checks file names (path.suffix == ".py"), so
                the same Python code under a .txt name passes.
                tests/behaviour.py:31-43 runs the program in rewardkit's Worker, which hides
                /tests but not Python: the grader image is python:3.12-slim
                (tests/Dockerfile:1) and the program's PATH includes /usr/local/bin
                (tests/behaviour.py:33). The Worker user must be able to start Python,
                because rewardkit starts its own sandbox with it (rewardkit 0.2.4,
                sandbox.py:175-202), so the submitted program can start it too.
How to fix:     Make sure the program cannot start Python, not just that no file ends in
                .py. For example, run the built binary as a user that cannot execute
                python3 (in my own task: uid 65534, Python not executable by others).
                This means running the binary outside rewardkit's Worker, which needs
                Python itself. A cheaper extra check: set the reward to 0 when the Go code
                can start programs (os/exec, syscall or os.StartProcess, seen with
                `go list -deps`) or when any file holds Python code under another name.
```

## Cheat 3 — Half port

```
What it does:   A Go program that ports only the easy rules of instruction.md:5 (small
                words, first/last word, capital first letter, words with an inner capital
                or letter.letter left alone, '-' and '/' pieces, small word after ": ").
                It skips the hard half on purpose: d'/l'/o' names, Mc/MC, Mr/Mrs/Ms/Dr,
                all-caps lines and initials, consonant-only acronyms, tabs, Unicode.
                On hand-made titles that use the skipped rules it is wrong, for example
                "o'neil" -> "O'neil" and "mcdonald" -> "Mcdonald".
Score:          reward 0.9997  (build 1, no_python 1, behaviour 0.9995 = 1999 of 2000)
Job folder:     jobs/2026-11-23__12-16-17
Why it worked:  The hidden exam never uses the skipped rules. behaviour.py:8-9 reads only
                hidden_inputs.txt, made by tests/gen.py from 21 small words, 64 normal
                words, 5 preserved words and 3 URLs (gen.py:15-105) in 9 kinds of title
                (gen.py:119-176). In the 2,000 hidden inputs there are 0 apostrophes,
                0 Mc words, 0 Mr/Mrs/Ms/Dr, 0 all-caps lines, 0 tabs or double spaces,
                0 digits and 0 non-ASCII characters. The one line it missed
                (line 1611, "crystal vs. v. at lazy if lazy") is an easy-rule bug.
How to fix:     A bigger, weirder exam that exercises every rule in instruction.md:5:
                apostrophe names, Mc/MC, Mr/Dr, all-caps lines with initials, consonant
                acronyms, Unicode letters and spaces, tabs, punctuation. For example the
                class kit's make_pool.py at 100,000 titles, with answers frozen twice.
```

## Other weak spots (read in the code, not run as cheats)

- **Internet is open during the agent run** (`task.toml:17` `network_mode = "public"`), and the hidden
  answers are committed in the class repo (`tests/data/hidden_expected.txt`). If the repo can be read
  without logging in, a solution could download them. Not tested. Fix: `network_mode = "no-network"`
  (the oracle `solve.sh` downloads nothing), or keep the answers out of anything the agent can reach.
- **The answer mode is not stated.** `instruction.md` never says whether the answers come from titlecase
  with or without the `regex` package. With the current ASCII-only exam this makes no difference, but it
  will with a bigger exam.
- **Strong part:** the program cannot read the exam while it is graded. rewardkit's Worker runs it as a
  fresh unprivileged user and keeps `/tests` private (rewardkit 0.2.4, `sandbox.py:79`, `:122`), and the
  agent container never gets `tests/` (`task.toml:8` `environment_mode = "separate"`).

**Highest score any cheat got: 1.0 (Cheat 2, Python inside).**
