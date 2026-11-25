# Day 6 Defence Report — Tannu Kumari (`ethara/titlecase-go`)

Attacker: **Siddharth Singh** (`training-3/SiddharthSingh/attack/ATTACK.md`, against my commit `0229b5f`).
Day 5 details: `HARDEN.md`.

## 1. Objective of Day 6

Day 6 proves that the hardened task works and defends it:

1. The reference solution (oracle) must still score **1.0**.
2. An agent that does nothing (NOP) must score **0.0**.
3. Each of my attacker's cheats must score **below 0.2**.
4. My attacker re-runs his cheats on the hardened task and may try one new cheat.

This report covers points 1–3 with saved reward files. Point 4 depends on Siddharth and is still open (see §7).

## 2. Results on the hardened task

All runs were made with Harbor on 2026-11-24, against the hardened task in `task/`. Each cheat ran
with `harbor run -a oracle` and the cheat's unchanged files as `solution/`. NOP used the `nop` agent.

| Run | build | no_python | behaviour | **Reward** | Target | Pass |
|---|---:|---:|---:|---:|---|---|
| Oracle | 1 | 1 | 1.0 | **1.0** | 1.0 | ✅ |
| NOP | 0 | 0 | 0 | **0.0** | 0.0 | ✅ |
| Cheat 1: visible answer lookup | 1 | 1 | 0.0 | **0.0** | < 0.2 | ✅ |
| Cheat 2: build-only no-op | 1 | 1 | 0.0 | **0.0** | < 0.2 | ✅ |
| Cheat 3: read verifier answers at runtime | 1 | 1 | 0.0 | **0.0** | < 0.2 | ✅ |
| Cheat 3 answer-access probe | 1 | 1 | 0.0 | **0.0** | < 0.2 | ✅ |

NOP scores 0 because the untouched Python repository has no `go.mod`, so the build gate fails.

Cheats 1–3 still build and pass the clean checks (build = 1, no_python = 1). They get 0 because they
produce no correct titlecase output, and building earns no points by itself.

## 3. Before and after hardening

Before: the task at commit `0229b5f`, which Siddharth attacked. I re-ran his cheats there, and my scores
match his `ATTACK.md`.

| Cheat | Before hardening | After hardening |
|---|---:|---:|
| 1 Visible answer lookup | 0.3333 | **0.0** |
| 2 Build-only no-op | 0.3333 | **0.0** |
| 3 Read verifier answers | **1.0** | **0.0** |
| 3 probe (new answer path) | — | **0.0** |

## 4. The three attacks and how each is blocked

### Cheat 1: visible answer lookup
- **What it does:** a Go program loads `lookup.json` (the 2,000 visible input/output pairs). It prints the
  stored answer for a known input and `UNKNOWN` for anything else.
- **Why it worked before:** the hidden inputs did not overlap the visible ones, so behaviour was 0.
  But the old reward was a weighted mean (`reward.toml`: build 1, no_python 1, behaviour 4). Building
  and deleting the `.py` files alone gave 2/6 = 0.3333.
- **How it is blocked now:**
  - Build and clean checks are gates, not points, so the reward is behaviour only.
  - The program runs in an empty jail, where `/workspace/repo/lookup.json` does not exist.
  - The old 2,000-line visible data is removed.

### Cheat 2: build-only no-op
- **What it does:** `func main() {}` plus deleting the `.py` files. No titlecasing at all.
- **Why it worked before:** the same weighted mean gave 0.3333 for building.
- **How it is blocked now:** the gated score. A program that builds but prints nothing scores 0.

### Cheat 3: read verifier answers at runtime
- **What it does:** ignores stdin and copies `/tests/data/hidden_expected.txt` to stdout.
- **Why it worked before:** the old `behaviour.py` ran the submitted binary inside the verifier container,
  as root, with `/tests` present. The binary could simply open the answer file, so it scored 1.0.
- **How it is blocked now:** the binary runs in a chroot jail as an unprivileged user, so `/tests` is not
  visible. The answer files are also readable by root only.
- **Why a probe was needed:** the new exam file is named `answers.txt`. So the unchanged cheat 3 would also
  fail just because the old file name is gone. To show that the **jail** blocks the attack, and not the
  rename, I ran a probe: the same program opening `/tests/data/answers.txt`. It scored 0.0, and its
  `verifier/run.err` reads `open /tests/data/answers.txt: no such file or directory`. The file exists in
  the verifier, but not inside the jail.

## 5. The defences

All of these are in `task/tests/test.sh`, `task/tests/Dockerfile` and `task/task.toml`.

| Defence | What it does | Where |
|---|---|---|
| **Gated scoring** | `reward = behaviour` only when build = 1 and clean = 1, otherwise `reward = 0`. Build and no_python earn nothing on their own. | `tests/test.sh:69-73` |
| **Chroot jail** | The port is built as a static binary (`CGO_ENABLED=0`) and run alone in an empty temporary folder. Only the binary is inside: no `/tests`, `/workspace`, `/proc`, Python or shell. Input comes on stdin, and output is compared outside the jail. | `tests/test.sh:52-66` |
| **Unprivileged execution** | `chroot --userspec=65534:65534` runs the port as uid/gid 65534 (nobody). It has no root rights and cannot escape the jail or read root-only files. | `tests/test.sh:57` |
| **Protected answer files** | `/tests/data` is `chmod 700` and its files are `chmod 600`, owned by root. This is a second layer if the jail were ever weakened. | `tests/Dockerfile:8` |
| **Clean checks** | No `.py` file in the repo, no `require` or `replace` in `go.mod`, no `vendor/`, no `import "C"`, and Go sources under 1 MB, so an answer table cannot be pasted into the code. Any failure scores 0. | `tests/test.sh:32-50` |
| **Strict output comparison** | Byte-for-byte line comparison, with `LC_ALL=C`. The score is `matched / max(expected lines, printed lines)`, so missing or extra lines cost points. | `tests/test.sh:59-63` |
| **No-network verifier** | The verifier runs with no network. The old rewardkit setup (`uvx`) is gone, so grading needs nothing from outside. | `task.toml` `[verifier] network_mode = "no-network"` |

## 6. The 100,000-input exam

The exam was built with the trainer's kit (`kit/make_pool.py`, `kit/answers.py`) in Linux containers.

| Item | Value |
|---|---:|
| Total inputs | 100,000 |
| Stable inputs (kept) | 100,000 |
| Unstable inputs (dropped) | 0 |
| Regex module used | False |
| Final oracle mismatches | **0** of 100,000 |

- **Source:** `measure/report.txt` and `measure/new-exam-100k/tannu-fixed.txt`.
- **Frozen twice:** `answers.py` runs the original twice (`PYTHONHASHSEED=1` and `2`) and keeps only
  inputs whose answers match. I also re-ran the whole script, and ran it a third time inside the agent
  image (`golang:1.23`). All three answer files are byte-identical (`measure/freeze-check.txt`).
- **Mode:** `re`. The `regex` module is not installed, so `REGEX_AVAILABLE = False`. This is stated in
  `task/instruction.md` §2. It matches the agent's environment, where `python3` has no `regex` module.

### Underscore-prefix bug in my original Go port

The new exam found a real bug in my own solution. It scored 0 wrong on the old 2,000-line exam, but
**857 of 100,000** wrong on the new one, all on words starting with `_`:

```
input '-lead _and/or MCDONALD by #life an} data'
want  '-Lead _and/or McDonald by #Life An} Data'
got   '-Lead _And/or McDonald by #Life An} Data'
```

- **Cause:** in `re` mode, Python's `CAPFIRST` pattern is `^[PUNCT]*?([\w])`. The prefix is lazy, and `_`
  counts both as punctuation and as `\w`. So Python treats `_` itself as the "first letter", and the word
  stays unchanged. My Go `capFirst` skipped all punctuation first, then capitalised the next letter.
- **Fix:** `capFirst` in `task/solution/main.go:322-337` now stops at the first `\w` character, even if it
  is also punctuation.
- **Result:** 0 of 100,000 wrong, and Harbor oracle reward 1.0.

## 7. Status of Siddharth's Day 6 re-attack

**Siddharth's fresh Day 6 re-attack and any new-cheat results have NOT yet been received.**

The scores in §2 come from my own runs of his original, unchanged Day 4 cheats on my hardened task.
They are not his re-run. When he adds his re-attack results to the end of his `ATTACK.md`, I will
review them, and this section will be updated with his scores and any new cheat.

## 8. Evidence files

All paths are relative to `training-3/TannuKumari/`.

**Proof (hardened task):**
- `proof/oracle-reward.json` (1.0)
- `proof/nop-reward.json` (0.0)
- `proof/cheat1-reward.json`, `proof/cheat2-reward.json`, `proof/cheat3-reward.json` (0.0 each)
- `proof/cheat3-answers-probe-reward.json` (0.0)
- `proof/job-folders.txt`: the Harbor job folder for every run. The job folders themselves are local
  and not pushed.

**Proof (old task, before hardening):**
- `proof/before/cheat1-reward.json` (0.3333)
- `proof/before/cheat2-reward.json` (0.3333)
- `proof/before/cheat3-reward.json` (1.0)

**Measurement:**
- `measure/report.txt`: kit freeze report (100,000 kept, 0 dropped, regex False)
- `measure/freeze-check.txt`: sha256 of the three frozen answer files and the exam files
- `measure/old-exam-2k/`: `tannu-original.txt`, `tannu-fixed.txt`, `uday-bhatnagar.txt`, `neha-gaur.txt`
- `measure/new-exam-100k/`: the same four files, plus `neha-gaur-vs-regex-mode.txt`

**Task and reports:**
- `task/tests/test.sh`, `task/tests/Dockerfile`, `task/task.toml`, `task/instruction.md`,
  `task/solution/main.go`
- `task/tests/data/inputs.txt`, `task/tests/data/answers.txt`: the 100,000-input exam
- `HARDEN.md`: the Day 5 hardening report
