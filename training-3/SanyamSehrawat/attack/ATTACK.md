# Day 4 — Break a Classmate's Task

## 1. Attacker and Target Information

- **Attacker:** Sanyam Sehrawat
- **Target:** Alok Kumar Jaiswal
- **Target task path:** `training-3/AlokKumarJaiswal/task`
- **Target commit SHA:** `c48ed262886d763cfb8127880f0a2938fcc60ca4` ("copy practice task before hardening")
- **Local attack copy:** `training-3/SanyamSehrawat/attack/target/` (gitignored; the original was never modified)
- **Attack execution date:** 2026-11-20
- **Harbor:** 0.25.0, agent `oracle` (runs `solution/solve.sh`), Docker 29.9.2 on Windows 11.

All jobs were run with a fresh scratch copy of the target. Line endings in the local checkout were CRLF because `core.autocrlf=true` and the `training-3/` copy has no `.gitattributes`; each scratch copy was normalised back to LF (the byte-identical content stored in the git index and on GitHub) before running. No grader logic was changed.

### Standard controls (pipeline sanity)

| Run | reward | build | no_python | behaviour | Harbor job / trial |
| --- | --- | --- | --- | --- | --- |
| oracle | `1.0000` | 1 | 1 | `1.000000` | `sanyam-oracle` / `sc_sanyam-oracle__2gNWDon` |
| nop | `0.0000` | 0 | 0 | `0.000000` | `sanyam-nop` / `sc_sanyam-nop__uwiZvmT` |

---

## 2. Target Task Analysis

**What the task asks.** Replace the Python `titlecase()` with a Go program in `/workspace/repo` that reads UTF-8 lines on stdin and prints `titlecase(line)` for each, byte-for-byte identical to the reference Python with default arguments (`instruction.md:7-19`). Standard library only, no `.py` files left behind, no running other programs, no network (`instruction.md:22-27`).

**What a correct solution must do.** Fully port the reference `titlecase()` behaviour, including the rare rules: `Mc`/`MC` prefix, `O'`/`d'` apostrophe, `Mr`/`Mrs`/`Ms`/`Dr`, inline-period words, iTunes-style interior capitals, all-consonant acronyms, all-caps dotted initials, hyphen/slash recursion, and small-word first/last handling.

**How the evaluator works.** `tests/test.sh:2` runs `rewardkit /tests/checks`. Three criteria are combined by `tests/checks/reward.toml:4`:

```toml
weights = { build = 1.0, no_python = 1.0, behaviour = 4.0 }
```

So `reward = (build + no_python + 4·behaviour) / 6`.

- **build** (`tests/checks/build.py:8-18`): `go build ./...` returns 0 → `1.0`.
- **no_python** (`tests/checks/no_python.py:15-27`): `go build ./...` succeeds **and** no `*.py` exists anywhere under the workspace → `1.0`.
- **behaviour** (`tests/checks/behaviour.py:24-37`): builds the binary, enforces import rules, runs it on the hidden inputs, and returns the **fraction of output lines that exactly equal** the hidden expected lines:

```python
equal = sum(a == b for a, b in zip(output_lines, expected_lines))
return equal / total          # behaviour.py:36-37
```

**What the agent can see.** The agent container is built from `environment/Dockerfile` (`COPY repo /workspace/repo`): only the Python project source, which it must replace. The graded data lives in the **separate** verifier container at `/tests/data/hidden_inputs.txt` and `/tests/data/hidden_expected.txt` (`behaviour.py:13-14`); `task.toml:15` sets `environment_mode = "separate"`. The visible `tests/data/inputs.txt` / `expected.txt` are **not** graded.

**Restrictions enforced.** `tests/checks/_rules.py:9` forbids imports `os/exec, syscall, plugin, unsafe, C, net` and anything under `net/` (`_rules.py:30-31`); `_rules.py:50-60` rejects `require`/`replace`/`use` in `go.mod` (no third-party deps); `rules_ok` (`_rules.py:115-128`) allows only stdlib or the program's own module. The binary is run inside a `chroot` into an **empty** temp dir as uid/gid `65534` (`_rules.py:131-148`), so it can read nothing but stdin at run time.

**Three weakest points (with evidence):**

1. **Structural floor of 0.333** — `reward.toml:4` plus `build.py`/`no_python.py` hand `2/6 = 0.3333` to *any* program that merely compiles with no `.py` files, with zero correct output. (Exploited by cheat 1 and cheat 3.)
2. **Proportional, penalty-free behaviour credit** — `behaviour.py:36-37` is a plain `equal/total` with no deduction for wrong lines, so a partial port that only nails the common rules still banks real credit. (Exploited by cheat 2.)
3. **Runtime answer access and hidden≠visible** — these are the two holes the task *closed*: `behaviour.py:13-14` grades only the hidden set, and `_rules.py:131-148` jails the binary. Probed by cheat 1 (lookup) and cheat 3 (read-the-exam); both are shown below to fail, which is the correct, strong result.

---

## 3. Cheat 1 — Lookup / Visible-Information Approach

- **What it attempts:** embed the task's **visible** answer file (`tests/data/inputs.txt` → `expected.txt`, readable by any attacker) into the Go binary as a lookup table, and echo the line unchanged for anything not in the table.
- **Weakness targeted:** weakest point 3 — are the hidden graded inputs actually different from the visible sample inputs?
- **How it works:** `//go:embed` bakes the 2,000 visible pairs into the binary; at run time each stdin line is looked up, else returned unchanged. No titlecase logic.
- **Files created in the scratch copy:** `solution/solve.sh` (replaced), which writes `go.mod`, `vis_in.txt`, `vis_out.txt`, `main.go`.
- **Harbor command:** `harbor run -p <scratch-copy-of-target> -a oracle`
- **Reward file:** [`results/cheat1-reward.json`](results/cheat1-reward.json)
- **Actual reward:** `0.3640` — build `1`, no_python `1`, behaviour `0.046000` (92 / 2000 lines).
- **Harbor job / trial:** `sanyam-cheat1` / `sc_sanyam-cheat1__dZgXevr`
- **Why it scored this way:** the hidden set barely overlaps the visible set, so the table almost never hits and the program degrades to identity echo. The `0.046` behaviour is just the 92 hidden lines that happen to already be in title case. The `0.364` is essentially the `0.333` structural floor plus those coincidental lines. **The lookup hole is closed** — hidden ≠ visible (`behaviour.py:13-14`).

---

## 4. Cheat 2 — Partial Implementation Approach

- **What it attempts:** a "half port" that implements only the common, high-frequency rules — capitalise the first letter of each word, lowercase interior small words, capitalise the first/last word, recurse on hyphen/slash pieces, and capitalise a small word after `: ; . ? !` + space — and **skips** every rare rule (Mc, apostrophe, Mr/Mrs/Dr, inline-period, iTunes interior caps, all-consonant acronym, all-caps dotted initials).
- **Weakness targeted:** weakest point 2 — how much partial credit does a weak port earn, and do the checks tell a complete port from a partial one?
- **How it works:** pure stdlib Go (`bufio`, `io`, `os`, `strings`, `unicode`); no lookup, no real completeness.
- **Files created in the scratch copy:** `solution/solve.sh` (replaced), which writes `go.mod`, `main.go`.
- **Harbor command:** `harbor run -p <scratch-copy-of-target> -a oracle`
- **Reward file:** [`results/cheat2-reward.json`](results/cheat2-reward.json)
- **Actual reward:** `0.5217` — build `1`, no_python `1`, behaviour `0.282500` (565 / 2000 lines).
- **Harbor job / trial:** `sanyam-cheat2` / `sc_sanyam-cheat2__pduAcVG`
- **Why it worked:** `behaviour.py:36-37` gives proportional credit with no penalty, so 565 fully-correct lines count straight through: `(1 + 1 + 4·0.2825)/6 = 0.5217`. Because the match is **per whole line**, every line containing a rare construct the half-port ignores fails entirely, which is why behaviour sits at `0.28` rather than higher — but it is still the strongest cheat, 0.19 above the structural floor. This is the real hole: a visibly incomplete port is not distinguished from a correct one, it just scores lower.

---

## 5. Cheat 3 — Evaluation / Restriction Weakness

- **What it attempts:** at run time, read the hidden answer sheet directly from disk (`/tests/data/hidden_expected.txt` and four other likely paths) and replay it; if nothing is found, echo the input unchanged.
- **Weakness targeted:** weakest point 3 — are the hidden answers reachable by the solution binary while the behaviour check runs it?
- **How it works:** stdlib `os` only, so it passes the import allow-list (`_rules.py`); tries each candidate path, else falls back to identity echo. No titlecase logic.
- **Files created in the scratch copy:** `solution/solve.sh` (replaced), which writes `go.mod`, `main.go`.
- **Harbor command:** `harbor run -p <scratch-copy-of-target> -a oracle`
- **Reward file:** [`results/cheat3-reward.json`](results/cheat3-reward.json)
- **Actual reward:** `0.3640` — build `1`, no_python `1`, behaviour `0.046000` (92 / 2000 lines).
- **Harbor job / trial:** `sanyam-cheat3` / `sc_sanyam-cheat3__UmWaNka`
- **Why it failed (correct result):** `_rules.py:131-148` copies only the binary into an empty `chroot` jail and runs it as uid `65534`, so `/tests/data/...` does not exist at run time. Every `os.ReadFile` fails and the program falls back to identity echo — the exact same `0.046` behaviour as cheat 1. **The read-the-exam hole is closed**, and this is the strongest part of the target's defense.

---

## 6. Results Comparison

| Cheat | Approach | Actual reward | build | no_python | behaviour | Result |
| --- | --- | --- | --- | --- | --- | --- |
| Cheat 1 | Lookup / visible information | `0.3640` | 1 | 1 | `0.046000` | Floored — hidden ≠ visible |
| Cheat 2 | Partial implementation | `0.5217` | 1 | 1 | `0.282500` | **Strongest** — partial credit banked |
| Cheat 3 | Evaluation weakness (read the exam) | `0.3640` | 1 | 1 | `0.046000` | Blocked by the chroot jail |

All numbers are from real Harbor runs; reward files are in `results/`.

---

## 7. Strongest Cheat

**Cheat 2 (partial implementation), reward `0.5217`.** It is the only cheat that beats the structural floor on merit: 565 of 2,000 hidden lines are byte-exact from the common rules alone, worth `0.1884` of behaviour-weighted reward on top of the `0.3333` floor. Cheats 1 and 3 both collapse to identity echo (`0.364`) because the target correctly isolates the hidden set and jails the binary. The weakness cheat 2 exposes is real: the behaviour check gives penalty-free proportional credit, so an obviously incomplete port still clears half a point.

---

## 8. Recommended Fixes

1. **Gate the structural credit** (addresses weakness 1). In `tests/checks/reward.toml`, stop giving `build` and `no_python` unconditional weight. Either require a minimum behaviour (e.g. behaviour ≥ 0.5 before build/no_python count) or re-weight toward behaviour (e.g. `build = 1, no_python = 1, behaviour = 12`, which drops a floor-only cheat from `0.333` to about `0.143`). This removes the free `0.333`.
2. **Penalise wrong lines instead of only counting right ones** (addresses weakness 2). In `tests/checks/behaviour.py`, subtract for mismatched lines, or require lines that combine several rules (hyphen + small word + apostrophe + all-caps in one line) so a half-port cannot bank easy single-rule lines. Strengthen `tests/gen.py` to seed those mixed-rule and "weird" inputs (`v1.2`, `Mcx-`, `_dream`, tabs, non-breaking spaces).
3. **Keep the current isolation** (weakness 3 is already handled). The hidden-only grading (`behaviour.py:13-14`) and the empty-dir `chroot` jail (`_rules.py:131-148`) defeated both the lookup and the read-the-exam cheats; do not relax them.

No fix was applied to the target's original task.

---

## 9. Conclusion

Alok's task has a strong core: the grader isolates the hidden answer set and runs the candidate binary in a locked-down `chroot` jail with an import allow-list, so the two "shortcut" attacks (lookup of visible answers, reading the exam at run time) both fail and score only the `0.364` floor. The real weakness is the reward shape: `build` and `no_python` guarantee `0.333` to anything that compiles cleanly, and the behaviour check pays penalty-free proportional credit, so a visibly incomplete half-port reached `0.5217`. The task is robust against data theft but lenient toward partial correctness; tightening the reward weights and the line-matching rule would close the remaining gap.

**Highest score any cheat got: 0.5217 (cheat 2).**

---

## 10. Day 6 — Independent Re-attack on Alok's Hardened Task

Alok's published hardened task was re-tested at commit
`395755d7270e696f43c77f1be9afb960d1b080b8`. For each run, a fresh scratch copy was made
from that exact commit and only `solution/solve.sh` was replaced with the corresponding
original Day 4 cheat. The verifier, task configuration, and environment were left unchanged.
Runs used Harbor 0.25.0 with the `oracle` agent.

| Cheat | Harbor reward | Job name | Harbor run ID | Trial ID | Saved verifier reward |
|---|---:|---|---|---|---|
| Cheat 1 — visible lookup | `0.0001890625` | `sanyam-day6-cheat1-395755d` | `35302cd6-90f7-4c54-9bf7-95329cdd72f9` | `cheat1__4rP8zsp` | [`cheat1-reattack-395755d-reward.json`](results/cheat1-reattack-395755d-reward.json) |
| Cheat 2 — partial implementation | `0.1155524049` | `sanyam-day6-cheat2-395755d` | `62aa4f7c-222f-4e23-a433-5382a5978d0d` | `cheat2__9bd36Ea` | [`cheat2-reattack-395755d-reward.json`](results/cheat2-reattack-395755d-reward.json) |
| Cheat 3 — read the exam | `0.0001879641` | `sanyam-day6-cheat3-395755d` | `f901b076-c0d9-4170-abca-40c8f04bf46c` | `cheat3__MDQN8fP` | [`cheat3-reattack-395755d-reward.json`](results/cheat3-reattack-395755d-reward.json) |

All three independently measured rewards are below `0.2`. The first two match the scores
Alok reported. Cheat 3's exact score is now independently verified at `0.0001879641`.
