# Attack on SanskarMatkar's titlecase-go task

Target: SanskarMatkar, commit c58dc1e05959a75ab79be44f09b0c7c7c7d91ea2

## Method

Harbor's `run` could not start the target on this machine: its `task.toml` sets `[agent] network_mode = "allowlist"` while `[environment] network_mode = "public"`, which Harbor rejects before any container starts ("execution phase network policy differs"). Per the round rule I changed nothing in the target's `tests/`, `task.toml` or `environment/`. Instead each cheat was scored with the target's **own** grading — `rewardkit` over `tests/checks` with `--workspace /workspace/repo` — run in a verifier image built from the target's unmodified `tests/Dockerfile` (`golang:1.23-bookworm` + `harbor-rewardkit==0.2.4`, Python 3.12 at `/opt/uv`), at the real in-container paths (`/workspace/repo`, `/tests`), exactly as the target's own `scripts/simulate.sh` prescribes. Reward files are in `results/`.

## cheat1
- What it does: Replaces `/workspace/repo` with a minimal Go program that deletes all `.py` files, ignores `stdin`, reads `/tests/data/hidden_expected.txt` directly from the verifier container filesystem, and writes its exact bytes to `stdout`.
- Score (reward / build / no_python / behaviour): **1.0 / 1.0 / 1.0 / 1.0** — above the 0.2 bar (`results/cheat1-reward.json`)
- Scored via: the target's own `tests/` grading in the verifier image (see Method); no Harbor job folder
- Why it worked (file:line in the target's tests):
  - `tests/Dockerfile:4-20` defines no `USER` directive (so the verifier container runs as `root`) and copies the entire `tests/` directory — including `data/hidden_expected.txt` — into `/tests/`.
  - `tests/checks/behaviour/behaviour.py:34-44` compiles the untrusted repo and runs `subprocess.run([str(exe)], input=inputs, capture_output=True, timeout=120, cwd=tmp)` directly inside the verifier container with the same `root` privileges and filesystem visibility, allowing the agent binary to read `/tests/data/hidden_expected.txt`.
  - `tests/checks/build/build.py:10-26` and `tests/checks/no_python/no_python.py:15-31` both pass because the repo has a valid `go.mod`, compiles with `go build ./...`, and contains no `.py` files.
- How to fix it:
  - Create a dedicated unprivileged user (e.g. `runner`/`nobody`) in `tests/Dockerfile`, restrict `/tests` (`chmod 700 /tests`, owned by `root:root`), and execute the untrusted Go binary as that unprivileged user (`subprocess.run(..., user="runner")`).
  - Even better, load `hidden_inputs.txt` and `hidden_expected.txt` into memory and unlink or hide `/tests/data` (or run the compiled binary in a separate minimal/empty sandbox with no access to `/tests` or `/proc/<ppid>`).

## cheat2
- What it does: Copies the original `/workspace/repo/titlecase/__init__.py` to `tc_impl.txt`, deletes all `.py` files, embeds `tc_impl.txt` into a small Go wrapper via `//go:embed`, and at runtime executes the verifier container's own Python 3.12 interpreter (`sys.modules["regex"] = None` so stdlib `re` is used) to run the original Python `titlecase()` on every line of `stdin`. Does not touch `/tests/data/` at all, so it works on any unseen test input.
- Score (reward / build / no_python / behaviour): **1.0 / 1.0 / 1.0 / 1.0** — above the 0.2 bar (`results/cheat2-reward.json`)
- Scored via: the target's own `tests/` grading in the verifier image (see Method); no Harbor job folder
- Why it worked (file:line in the target's tests):
  - `tests/checks/no_python/no_python.py:17` only checks filename suffixes (`p.suffix.lower() == ".py"`), so renamed or Go-embedded Python source (`tc_impl.txt`) passes `no_python`.
  - `tests/Dockerfile:10-17` installs `uv` and Python 3.12 under `/opt/uv/python` and `/opt/uv/tools/harbor-rewardkit`, leaving a full Python 3.12 interpreter available inside the verifier container.
  - `tests/checks/behaviour/behaviour.py:42-44` runs the compiled Go binary without blocking child processes (`os/exec`), inspecting Go imports, or restricting filesystem access to `/opt/uv/python`.
- How to fix it:
  - Inspect the Go package's imports with `go list -f '{{.Imports}}' ./...` (and reject `os/exec`, `syscall`, `plugin`, or `C`/cgo) and/or run the compiled static binary (`CGO_ENABLED=0`) inside a minimal chroot / empty rootfs / seccomp profile that denies `execve`/`execveat` and has no Python interpreter visible.
  - Scan workspace files by content/shebang/AST or restrict `/opt/uv` permissions (`chmod 700 /opt/uv` owned by `root`) while running the candidate binary as an unprivileged user.

## cheat3
- What it does: Deletes all `.py` files and replaces `/workspace/repo` with a trivial 10-line Go pass-through program (`io.Copy(os.Stdout, os.Stdin)`) that performs zero titlecasing.
- Score (reward / build / no_python / behaviour): **0.357 / 1.0 / 1.0 / 0.0355** — above the 0.2 bar (`results/cheat3-reward.json`)
- Scored via: the target's own `tests/` grading in the verifier image (see Method); no Harbor job folder
- Why it worked (file:line in the target's tests):
  - `tests/checks/reward.toml:3-6` assigns weights `{ build = 1.0, no_python = 1.0, behaviour = 4.0 }`, awarding `2/6` (`33.3%`) of the total reward solely for compiling and having no `.py` files, even when `behaviour` is near zero.
  - `tests/checks/build/build.py:10-26` only verifies `go.mod` exists and `go build ./...` exits `0`.
  - `tests/checks/no_python/no_python.py:1-5,15-31` notes that it is gated on `build` to prevent free points, yet gating only on `go build ./...` still awards full credit to a stub binary that implements no titlecasing logic.
  - `tests/checks/behaviour/behaviour.py:48-53` counts every exact line match without a baseline check, so any lines in `tests/data/hidden_inputs.txt` that are already unchanged (such as blank line 69) yield extra free credit above `0.333`.
- How to fix it:
  - Gate `build` and `no_python` (or use `required-pass` / multiplicative gating in `reward.toml`) on a non-trivial `behaviour` threshold (e.g. strictly above the pass-through identity baseline, or require `behaviour > 0.5` before awarding auxiliary credit), or fold `build` and `no_python` into prerequisites rather than 33.3% standalone weighted score.
