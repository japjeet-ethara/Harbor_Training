# Day 5 Harden Report — Tannu Kumari (`ethara/titlecase-go`)

Attacker: **Siddharth Singh**. His report is `training-3/SiddharthSingh/attack/ATTACK.md`,
against my commit `0229b5f5f5d978c4958230bb07f7cac5b9c4f894`.

## 1. Result

| Run | Before (task at `0229b5f`) | After (hardened) | Target | Pass |
|---|---:|---:|---|---|
| Oracle | — | **1.0** | 1.0 | ✅ |
| NOP | — | **0.0** | 0.0 | ✅ |
| Cheat 1: visible answer lookup | 0.3333 | **0.0** | < 0.2 | ✅ |
| Cheat 2: build-only no-op | 0.3333 | **0.0** | < 0.2 | ✅ |
| Cheat 3: read verifier answers at runtime | **1.0** | **0.0** | < 0.2 | ✅ |
| Cheat 3 probe (pointed at the new `/tests/data/answers.txt`) | — | **0.0** | < 0.2 | ✅ |

I re-ran all three of Siddharth's cheats on `0229b5f` myself, and my scores match his. All runs used
`harbor run -a oracle` with the cheat's files as `solution/` (the `nop` agent for NOP). I did not change
the cheats. The reward files are in `proof/` (`proof/before/` holds the re-runs on the old task), and
the job folders are listed in `proof/job-folders.txt`.

The new exam file is named `answers.txt`, not `hidden_expected.txt`. So the unchanged cheat 3 would
fail just from that rename. To prove the **jail** closes the hole, and not the rename, I ran a probe:
the same program, but opening `/tests/data/answers.txt`. It also scored 0.0, and its
`verifier/run.err` says `open /tests/data/answers.txt: no such file or directory`. The file does exist
in the verifier, just not inside the jail.

## 2. Siddharth's cheats: why they worked

| # | What it does | Score | Why it worked (old task, `0229b5f`) |
|---|---|---:|---|
| 1 | Go program answers from a `lookup.json` of the 2,000 visible input/output pairs and prints `UNKNOWN` for everything else | 0.3333 | The hidden set does not overlap the visible one, so behaviour was 0. But `tests/checks/reward.toml:4` (`weights = { build = 1.0, no_python = 1.0, behaviour = 4.0 }`) gave 2/6 of the reward for building and deleting `.py` files alone. |
| 2 | `func main() {}`, plus deleting the `.py` files | 0.3333 | Same weighted mean, `reward.toml:4`: build + no_python = 2/6 for zero titlecasing. |
| 3 | Ignores stdin and copies `/tests/data/hidden_expected.txt` to stdout | **1.0** | `tests/checks/behaviour/behaviour.py:37-39` ran the submitted binary with `subprocess.run` inside the verifier container, as root, with `/tests` present (`tests/Dockerfile:7` `COPY . /tests/`). The binary could open the answer file named at `behaviour.py:9`. |

A side finding: the task as pushed on `training-3` before this change could not be graded at all.
The `task/` copy added in `d436178` left out `tests/checks/build/`, but `reward.toml` still weighted `build`.
So every run, even the oracle, ended with `RewardFileNotFoundError`
(`ValueError: unknown [[reward]].weights inputs: 'build'`). That's why I re-ran the cheats on `0229b5f`,
the commit Siddharth actually attacked.

## 3. What I changed to close them

All of these are in `task/`. The rewardkit checks are replaced by one bash verifier, `tests/test.sh`,
so grading no longer needs `uvx` or the network.

| Fix | Where | Closes |
|---|---|---|
| **Gated score.** `reward = behaviour` only if build = 1 and clean = 1, otherwise `reward = 0`. Build and no_python give no points of their own. | `tests/test.sh:69-73` | 1, 2 |
| **Jail.** The port is built to a static binary (`CGO_ENABLED=0`, `test.sh:10`) and run alone with `chroot --userspec=65534:65534` in an empty temp folder. Only the binary is inside: no `/tests`, `/workspace`, `/proc`, Python or shell. Stdin is the exam, and stdout is compared outside the jail. | `tests/test.sh:52-66` | 3 (and 1: `lookup.json` cannot be opened in the jail) |
| **Locked answers.** `/tests/data` is `chmod 700` and the files are `600`, owned by root, as a second layer if the jail were ever weakened. | `tests/Dockerfile:8` | 3 |
| **Clean gate.** No `.py` anywhere in the repo, no `require`/`replace` in `go.mod`, no `vendor/`, no `import "C"`, and Go sources under 1 MB, so a pasted answer table can't hide in the code. | `tests/test.sh:32-50` | 1, cgo `.incbin` tricks |
| **Strict line count.** The score is `matched / max(expected lines, printed lines)`, so extra or missing lines cost points. | `tests/test.sh:59-63` | padding tricks |
| **No verifier network.** | `task.toml` `[verifier] network_mode = "no-network"` | — |
| **Old data removed.** The 2,000-line visible and hidden files and `gen.py` are deleted. Only the new `inputs.txt` + `answers.txt` remain. | `tests/data/` | 1 |
| **Clear rules.** `instruction.md` now states the mode, the jail, the hard rules, and that breaking any rule scores 0. | `instruction.md` | — |
| **LF line endings.** `.gitattributes` forces LF, because on Windows `core.autocrlf=true` checked the scripts out as CRLF, which breaks `bash` in the container. | `.gitattributes` | — |

## 4. A real bug in my Go solution, found by the new exam

My oracle scored 1.0 on the old 2,000-line exam but got **857 of 100,000** wrong on the new one.
All the failures were words starting with `_`:

```
input '-lead _and/or MCDONALD by #life an} data'
want  '-Lead _and/or McDonald by #Life An} Data'
got   '-Lead _And/or McDonald by #Life An} Data'
```

The cause: in `re` mode, `CAPFIRST = ^[PUNCT]*?([\w])` (`environment/python-titlecase/titlecase/__init__.py:48`).
The prefix is **lazy** (`*?`), and `_` is both in `PUNCT` and in `\w`. So Python captures the `_` itself as
the "first letter" and uppercases it, which leaves the word unchanged. My Go `capFirst` skipped all
punctuation greedily first, then capitalised the next letter. The fix, in `solution/main.go:322-337`, walks
the word and stops at the first `\w` rune, even if that rune is also punctuation. After the fix:
**0 of 100,000 wrong**.

## 5. The 100,000-input exam

I used the trainer's kit unchanged (`kit/` is identical to `06-kit`). I ran everything in Linux
containers, because Windows Python writes CRLF line endings.

1. **Pool:** `python -I kit/make_pool.py 100000 1 pool.txt` (seed 1) gives 100,000 unique lines.
2. **Answers:** `python -I kit/answers.py task/environment/python-titlecase pool.txt out/`, run with
   Python 3.12 (`python:3.12-slim`) on the exact titlecase source in `environment/`.
3. **Frozen twice:** `answers.py` runs the original twice, with `PYTHONHASHSEED=1` and `2`, and keeps
   only lines that match. Report: 100,000 kept, 0 dropped, `regex module used False` (`measure/report.txt`).
   I then ran the whole script a second time, and a third time inside the task's own agent image
   (`golang:1.23`, Python 3.11). All three `answers.txt` are byte-identical, with sha256 `c898bf68…`
   (`measure/freeze-check.txt`).
4. The two exam files are `task/tests/data/inputs.txt` and `task/tests/data/answers.txt`.

**Mode: `re`** (no `regex` module, `REGEX_AVAILABLE = False`), stated in `instruction.md` §2. Why:
- The agent's environment (`golang:1.23`) has `python3` **without** `regex`. So running the original
  there gives exactly these answers, and the agent can check its port against the real thing.
- My oracle matches `re` mode on 100,000/100,000 inputs. It would get 2,221 wrong in `regex` mode.
  The two modes differ on 3,053 of the 100,000 lines, so the mode had to be stated.

## 6. Old exam vs new exam (three ports + my fix)

Each port was built with `CGO_ENABLED=0` in `golang:1.23` and scored with `kit/compare.py <exam> <output> 2000`.
Results are in `measure/old-exam-2k/` and `measure/new-exam-100k/`.

| Port | Source | Wrong on old 2k exam | Wrong on new 100k exam (`re`) | Chance a random 2k suite misses it |
|---|---|---:|---:|---:|
| **Tannu, original** (before the fix) | my `task/solution` at HEAD before Day 5 | 0 / 2,000 | **857** | 0% |
| **Tannu, fixed** (current oracle) | my `task/solution` now | 0 / 2,000 | **0** | — |
| Uday Bhatnagar | `Uday-Bhatnagar/task/solution` @ `3801b4d` | 0 / 2,000 | **0** | — |
| Neha Gaur | `NehaGaur/task/solution` @ `aa58f07` | 0 / 2,000 | **3,520** | 0% |

- All four ports looked perfect on the old exam. The new exam exposes two of them.
- My original port: the `_` bug in §4.
- Neha's port mostly follows **`regex`** mode. Its first diffs are `v1.2` becoming `V1.2`. Against
  `regex`-mode answers it is still wrong on 488 / 100,000
  (`measure/new-exam-100k/neha-gaur-vs-regex-mode.txt`). That's the same 488 that
  Aaditya Markande measured for her port, so the measurement is reproducible.
- Uday's port is correct on all 100,000 in `re` mode.

## 7. Files

- `task/`: the hardened task (`tests/test.sh`, `tests/Dockerfile`, `tests/data/{inputs,answers}.txt`,
  `instruction.md`, `task.toml`, `solution/main.go`)
- `proof/`: reward files for oracle, nop, cheats 1–3 and the cheat 3 probe; `proof/before/` holds the
  re-runs on `0229b5f`; `proof/job-folders.txt`
- `measure/`: compare results per port and exam, `report.txt`, `freeze-check.txt`
- `kit/`: the trainer's kit, unchanged

## 8. What I learned

1. **A cheat that reads the answer key wins outright.** Running the candidate in the same container
   as the answers handed out 1.0. The fix is isolation, not a better file name.
2. **Free points add up.** Weighted build and no_python points gave an empty program 0.333. They must be gates.
3. **2,000 inputs proved nothing.** Four ports scored perfectly on my old exam. On 100,000, two were
   wrong, including my own oracle, which failed on a rare `_` prefix.
