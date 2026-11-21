# ATTACK.md: 3 cheats on Shashwat Suman's task (`titlecase-go`)

Attacker: Ansh Dixit  |  Target: Shashwat Suman  |  Commit copied: `dcbe88466f7281cfb7969a6ff9288f2be331de32`
(branch `training-3`, folder `ShashwatSuman/titlecase-go/`)

> **How these numbers were produced (please read).** The sandbox I worked in had no Docker, so I could not
> call `harbor run`. Instead I rebuilt the verifier by hand: Go 1.23, the same `harbor-rewardkit==0.2.4`
> install as `tests/Dockerfile:10-12` (same `UV_TOOL_DIR=/opt/uv-tools`), the target's **unchanged**
> `tests/` copied to `/tests`, the repo copied to `/workspace/repo`, then the target's own
> `tests/test.sh` run unchanged. My replica scored the target's own oracle **1.0** and a do-nothing run **0.0**,
> so the replica agrees with the task on the two known cases. The "Job folder" lines below name my
> local replica runs, **not** Harbor job folders. Run `attack/run-cheats.sh` on a machine with Docker to
> get real Harbor job folders, then paste them in where marked `TODO`.

Summary table

| Cheat | Idea | Reward | build | no_python | behaviour |
|-------|------|--------|-------|-----------|-----------|
| 1 | Read the exam at run time | **1.0** | 1 | 1 | 1.0 |
| 2 | Python inside (hidden under a `.txt` name) | **1.0** | 1 | 1 | 1.0 |
| 3 | Delete trick + empty Go program | **0.3333** | 1 | 1 | 0.0 |

Baselines (same replica): target's own oracle = 1.0, `nop` (do nothing) = 0.0.

---

## Cheat 1: Read the exam

**What it does:** Ports nothing. `solve.sh` builds a Go program that, when the verifier runs it, searches `/tests`
for `hidden_inputs.txt` and `hidden_expected.txt`, builds an input to answer map, and prints the stored answer
for each stdin line. It touches only `/workspace/repo`.

**Score:** reward **1.0** (build 1, no_python 1, behaviour 1.0)

**Job folder:** local replica `jobs-local/cheat1` (not a Harbor job). TODO: replace with the Harbor job folder from `run-cheats.sh`.

**Why it worked:**
- `tests/Dockerfile:18` (`COPY . /tests/`) puts the hidden answers inside the verifier image.
- `tests/behaviour.py:13` and `:22-23` read them from `/tests/data/hidden_*.txt`.
- `tests/behaviour.py:34-36` then runs the **agent's own binary** (`subprocess.run([str(binary)], ...)`) in that same
  container, as the same (root) user, with no sandbox. So the program under test can open the answer sheet.
- The comments at `task.toml:32-33` and `tests/behaviour.py:3-4` say the agent can never see the hidden answers.
  That is true for the agent's container, but not for the agent's program, which runs in the verifier container.
  `task.toml:36` (`no-network`) blocks the network, not local file reads.

**How to fix:** Never run the agent's binary where the answers are readable. Best: store only a SHA-256 of each expected line in
`tests/data/` and compare hashes in `behaviour.py` (the binary can then never print the answer). Also run the binary
as an unprivileged user (e.g. `setpriv --reuid=65534 ...`) with `/tests` set to mode `700`.

---

## Cheat 2: Python inside

**What it does:** Ports nothing. Copies `titlecase/__init__.py` to `titlecase_src.txt`, deletes every `.py`, and builds a Go
wrapper that `go:embed`s the text, writes it back to a temp folder as `__init__.py` at run time, and runs it with a
Python that is already in the verifier image: `/opt/uv-tools/harbor-rewardkit/bin/python`. That interpreter
already has the `regex` package, so it matches the exam's reference mode.

**Score:** reward **1.0** (build 1, no_python 1, behaviour 1.0). Extra check: with a plain Python that has **no** `regex`, the same
original code gets 1852/2000 hidden titles right (0.926), so reward ~0.95. It stays high even if `regex` is missing.

**Job folder:** local replica `jobs-local/cheat2` (not a Harbor job). TODO: replace with the Harbor job folder.
Note: in my replica the rewardkit venv's Python links to the system 3.12. In the real image `uv` may fetch its own Python into
`/opt/uv-python`, but the venv path `/opt/uv-tools/harbor-rewardkit/bin/python` is the same. Please confirm with the real Harbor run.

**Why it worked:**
- `tests/no_python.py:16` only looks for the file extension `*.py` (`workspace.rglob("*.py")`). The same source under another
  name passes. The docstring at `tests/no_python.py:1-5` only guards against "delete files and build nothing".
- `tests/Dockerfile:6-10` installs Reward Kit (a Python tool, with `regex`) into `/opt/uv-tools` in the same image that
  `tests/behaviour.py:34-36` uses to run the binary, so a Python is always available to the cheat.
- `tests/behaviour.py:34-36` has no sandbox and no check that the binary stays pure Go.

**How to fix:** (1) Run the binary in a clean container or user that has no Python (e.g. `chmod 700 /opt/uv-tools /opt/uv-python` and run as `nobody`).
(2) Make `no_python.py` stricter: fail if any file contains Python code (shebang, `def `, `import `, `titlecase`), if any non-Go file is
embedded, or if the Go code imports `os/exec` or `syscall`.

---

## Cheat 3: Delete trick + empty program

**What it does:** Ports nothing and answers nothing. Writes `go.mod` and `package main; func main() {}`, deletes all
`.py` files, builds. The aim is the free "build" and "no_python" points.

**Score:** reward **0.3333** (build 1, no_python 1, behaviour 0.0)

**Job folder:** local replica `jobs-local/cheat3` (not a Harbor job). TODO: replace with the Harbor job folder.

**Why it worked:**
- `tests/build.py:12-29` only needs `go.mod` (no `require`) and `go build ./...` to pass. An empty `main` passes.
- `tests/no_python.py:16-28` gives its point when no `.py` exists and the build passes. An empty `main` also passes.
  The docstring at `tests/no_python.py:3-5` thinks the build condition stops free points, but it does not.
- `tests/reward.toml:11` (weights 1 / 1 / 4) means those two free checks are worth 2/6 = 0.333 on their own.
  The comment at `tests/reward.toml:6` says "build only → ~0.17", which forgets that `no_python` is also free.

**How to fix:** Gate the two cheap checks on real behaviour: make `build` and `no_python` score 0 unless the program gets a minimum
share (for example >= 50%) of some titles right, or use `reward = behaviour * build * no_python`. Or lower their weights so the
free total is below 0.2 (e.g. 0.2 / 0.2 / 4 gives about 0.09).

---

## Other weak points noticed (not used as cheats)

- The hidden exam is only **2000** titles (`tests/data/hidden_inputs.txt`, 2000 lines, 0 overlap with the visible 2000), which is
  small for catching rare bugs (guide Lesson 2).
- `tests/behaviour.py:39-40` compares line by line by position and ignores extra output lines. Harmless now, but fragile.

---

**Highest score any cheat got: 1.0 (Cheat 1 and Cheat 2).**
