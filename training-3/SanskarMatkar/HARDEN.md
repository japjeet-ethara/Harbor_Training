# HARDEN — Sanskar Matkar's titlecase-go task (Day 5)

Attacker: Sugandh Sharma (`training-3/SugandhSharma/attack/ATTACK.md`).
Mode of the new exam: **titlecase WITHOUT `regex`** (`re` fallback), now stated in bold in
`task/instruction.md` §4.

## Step 5.1 — Re-running the attacker's cheats

Sugandh could not start my task in Harbor. Her Harbor version refused it because
`[environment] network_mode = "public"` was broader than `[agent] network_mode = "allowlist"`,
so she scored the cheats by running `rewardkit` by hand. My Harbor (0.26.0) starts it, so I
re-ran her three `solve.sh` files unchanged on a copy of my task as it was before hardening
(only `solution/` replaced). I got **the same numbers she reported**:

| Cheat | Sugandh's number | My re-run | Job folder |
|---|---|---|---|
| 1 — read `/tests/data/hidden_expected.txt` | 1.000 | 1.000 (1/1/1.0) | `jobs/2026-11-23__11-42-16` |
| 2 — Go wrapper runs the verifier's Python 3.12 | 1.000 | 1.000 (1/1/1.0) | `jobs/2026-11-23__11-44-50` |
| 3 — echo program + delete `.py` | 0.357 | 0.357 (1/1/0.0355) | `jobs/2026-11-23__11-47-32` |

## Holes closed

```
Cheat 1: was 1.000, now 0.000 (jobs/2026-11-23__12-06-39)
  fix: the agent's program runs in an EMPTY chroot as nobody with an empty environment
       (tests/lib/grade.py, run_in_jail). Inside the jail only the static binary exists,
       so /tests does not exist for it: it prints 0 lines.
Cheat 2: was 1.000, now 0.000 (jobs/2026-11-23__12-10-46)
  fix: three independent locks, each enough on its own:
       (a) the jail has no Python, no shell, no other file, so there is nothing to exec;
       (b) direct imports of os/exec, syscall, unsafe, plugin, net..., cgo -> 0 on every check;
       (c) no_python now also looks at CONTENT: a file containing Python-only markers
           (def titlecase(, REGEX_AVAILABLE, import regex, python shebang, sys.modules[)
           counts as Python even when it is called tc_impl.txt or sits inside main.go.
Cheat 3: was 0.357, now 0.010 (jobs/2026-11-23__12-15-13)
  fix: build and no_python pay only when behaviour >= 0.5 (grade.gated). An echo
       program now keeps only its own behaviour share: 1,528 of 100,000 = 0.0153 -> 0.0102.
Harbor start-up: [environment] network_mode "public" -> "no-network", so Harbor versions
  without dynamic network policy can start the task (task.toml).
```

Oracle and nop on the hardened task, in Harbor:

| Run | Reward | Job folder |
|---|---|---|
| oracle | **1.0** (100,000 / 100,000 matched) | `jobs/2026-11-23__12-00-41` |
| nop | **0.0** | `jobs/2026-11-23__12-04-01` |

Files: `proof/oracle-reward.json`, `proof/nop-reward.json`, `proof/cheats-reward.txt`.

### A bug I found in my own repo while hardening

The repo-root `.gitignore` ignores every path called `build`. Because of that, my Day 4
"copy practice task" commit **silently left out `tests/checks/build/build.py`**. The
pushed copy of my task had no build check at all. My local folder had it, so my own runs
looked fine. Fixed with `!task/tests/checks/build/` in `SanskarMatkar/.gitignore`, and
the file is now committed.

## Exam: before and after

Old exam: 2,000 hidden inputs (my own `tests/gen.py`).
New exam: **100,000 inputs, mode: re** (no `regex`), from the trainer's `kit/`:

```
make_pool.py 100000 1 pool.txt          (python:3.14-slim, --network none)
answers.py   <python-titlecase> pool.txt key
  -> pool 100000, kept 100000, dropped 0, regex module used False   (kit/report.txt)
```

I added one word bank, `EXTRA`, to `kit/make_pool.py`. It holds the families my old exam
had that the trainer's banks lack (curly quotes, `…`, `«the»`, `Œuvre`, `Łódź`, `A.é.`,
`O'NEILL''`, `mc_x`, `a--b`, `state-of-the-art`, ...), plus the section 1 failure words
(`Mcx-`, `_dream`, `v._`, `X-RAY`, `as!`). The trainer's pool also has `ı`, `ß`, Greek and
Cyrillic, which my old instruction did not allow. I widened `instruction.md` §4 to match,
because the answers must stay what the original returns.

The ports were built and run as in step 5.3: `golang:1.23`, `--network none`, one title per
line on stdin. Old-exam numbers come from the same binaries run on my old
`hidden_inputs.txt` / `hidden_expected.txt`.

| Port | Wrong on new exam | Old exam caught it? | Chance 2K random misses it |
|---|---|---|---|
| my oracle (`task/solution`) | **0** / 100,000 | n/a (0 / 2,000 wrong) | n/a |
| Tanya Shrivastava (`TanyaShrivastava/task/solution`) | 4,711 | yes (86 / 2,000 wrong) | 0% |
| Sugandh Sharma (`SugandhSharma/task/solution`) | 9,613 | yes (136 / 2,000 wrong) | 0% |

Raw output: `measure/my-oracle.txt`, `measure/tanya.txt`, `measure/sugandh.txt`.

**Tanya's 4,711 are all mode differences (Lesson 3).** Her task says the answers come from
titlecase **with** `regex`. I froze a second answer set from the same pool with `regex`
installed. On it her port gets **0 wrong** (`measure/tanya-vs-regex-mode.txt`). On this pool
the two modes give different answers for exactly 4,711 titles. Her port is correct, but for
the other mode, and my old instruction and exam would have marked it just as wrong.

**Sugandh's 9,613 are real bugs.** Her port lower-cases or leaves non-Latin first letters
alone. For example `ıstanbul` should become `Istanbul`, `ÉLAN` should become `Élan`, and
`дом` should become `Дом` (examples in `measure/sugandh.txt`).

## What I learned (3 lines)

1. My exam's worst holes were not in its inputs but in **where the program runs**: same
   container, root, Python on disk. Two cheats got a full 1.0 with zero porting.
2. Points for "builds" and "no Python" are free money unless they are gated on real
   behaviour. Filename checks are weaker than they look: a renamed file defeats them.
3. Say the mode: a perfect port of the other mode looks like a 4.7%-broken port.
