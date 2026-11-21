# Attack report — Adarsh Sahani's `titlecase-go`

**Attacker:** Gunjit **Target:** Adarsh Sahani — `AdarshSahani/titlecase-go`
**Commit attacked:** `5fd8c5bf14ffa683fb80b9d85e5eea390133d708` (see `TARGET.txt`)
**When:** 2026-11-20 (job-folder timestamps below) **Where:** local Harbor 0.25.0 + Docker, on a throwaway copy of the target in `attack/target/` (never his real folder)
**How:** each cheat is a `solution/solve.sh` run by Harbor's `oracle` agent on a scratch copy. Only `solution/` is ever written — `tests/`, `task.toml` and `environment/` are untouched.

## Headline

**Highest score any cheat got: `cheat1` = 1.000 — a full pass with no title-casing at all.** It reads his hidden answer key off the disk and prints it. Four of the five cheats clear the 0.2 bar.

## Baseline (reference runs on his unchanged task)

| Run | behaviour | build | no_python | reward | job folder |
|---|---|---|---|---|---|
| his oracle (real Go port) | 1.00 | 1.00 | 1.00 | **1.000** | `oracle-20261120-085956` |
| nop (does nothing) | 0.00 | 0.00 | 0.00 | **0.000** | `nop-20261120-090045` |
| his own cheat (`cheat/solve.sh`) | 0.00 | 1.00 | 0.00 | **0.167** | `his-cheat-20261120-090126` |

His task runs correctly (oracle 1.0, nop 0.0) once the data files are read with Unix line endings. See "Note on line endings" at the end.

## Cheats

Reward files are in `results/cheatN-reward.json`; screenshots in `screenshots/`.

### Cheat 1 — Read the exam  ⟶ reward 1.000  (CRITICAL)
**What it does:** writes a Go program that ignores stdin and prints the contents of `/tests/data/hidden_expected.txt` (the hidden answer key), then deletes the `.py` files.
**Score:** behaviour 1.00, build 1.00, no_python 1.00 → **reward 1.000**. Job: `cheat1-20261120-085536`.
**Why it worked:** the verifier runs the submitted binary with **no sandbox and no user drop**, as root, inside the container that also holds the answer key:
- `tests/Dockerfile:11` → `COPY . /tests/` puts `hidden_expected.txt` in the verifier image, world-readable.
- `tests/checks/behaviour/behaviour.py:54-59` runs `subprocess.run([str(BINARY)], input=input_bytes, capture_output=True, timeout=180)` — no `user=`, no `cwd` isolation, no stripped environment. The binary runs as root and can open any file.
So the "port" just copies the file the grader is about to compare against. Output equals expected byte for byte → 1.0.
**How to fix:** run the submitted binary as an unprivileged user that cannot read the answers, e.g. `subprocess.run([BINARY], ..., user="nobody")` after `chmod -R go-rwx /tests`, and strip its environment. Better still, grade in a stage that holds no answer files on disk.

### Cheat 2 — Empty build + delete Python  ⟶ reward 0.333
**What it does:** writes a Go program that compiles but does nothing (`func main(){}`), and deletes the `.py` files. No porting.
**Score:** behaviour 0.00, build 1.00, no_python 1.00 → **reward 0.333**. Job: `cheat2-20261120-085623`.
**Why it worked:** `build` and `no_python` are scored on their own and pay out for zero real work:
- `tests/checks/build/build.py` = `rk.command_succeeds("go build ./...")` — any compiling program scores 1.
- `tests/checks/no_python/no_python.py:24-28` scores 1 when the build passes and no `.py` remains — it never checks a single title.
- `tests/checks/reward.toml` weights these 1 + 1 of 6, so doing nothing floors at 2/6 = 0.333.
**How to fix:** gate `build` and `no_python` on real behaviour — only award them when `behaviour` is above a threshold (e.g. 0.95), or fold "builds" and "no .py" into the behaviour criterion so they are worth nothing alone.

### Cheat 3 — Visible lookup table  ⟶ reward 0.491
**What it does:** embeds the **visible** `inputs→expected` pairs in a Go map and echoes anything not in it.
**Score:** behaviour 0.236, build 1.00, no_python 1.00 → **reward 0.491**. Job: `cheat3-20261120-085708`.
**Why it worked:** the visible set is useless — his hidden inputs share **0** lines with the visible ones (`tests/gen.py` draws disjoint sets), so the map never hits and the cheat collapses to the echo baseline (0.236). The 0.491 is almost entirely the free `build`+`no_python` points from Cheat 2 plus identity echo. This is the *good* news for the target: the visible/hidden split is solid.
**How to fix:** nothing needed for the split itself; the score is carried by the Cheat 2 and Cheat 5 holes, so fixing those drops this too.

### Cheat 4 — Build-only, keep the Python  ⟶ reward 0.167
**What it does:** an empty compiling program that leaves every `.py` file in place.
**Score:** behaviour 0.00, build 1.00, no_python 0.00 → **reward 0.167**. Job: `cheat4-20261120-085816`.
**Why it worked:** `build` pays out on its own (`build.py`) with no porting and no cleanup. This is the single cheat **below** 0.2 — reported honestly: the `build` point alone is not enough to pass, but it should still not be free.
**How to fix:** same as Cheat 2 — do not score `build` independently of behaviour.

### Cheat 5 — Identity echo  ⟶ reward 0.491
**What it does:** prints every input line unchanged (no title-casing), deletes the `.py` files.
**Score:** behaviour 0.236, build 1.00, no_python 1.00 → **reward 0.491**. Job: `cheat5-20261120-085910`.
**Why it worked:** `behaviour` (`behaviour.py:66-72`) gives partial credit for exact line matches with no floor, and 23.6% of his hidden titles are already equal to their title-cased form (short words, already-cased input, symbols). Combined with the free 0.333 this reaches 0.491.
**How to fix:** harden the exam with weirder, bigger inputs so the echo baseline drops, and gate the free points (Cheat 2 fix). An identity port should score near 0.

## Summary

| Cheat | reward | over 0.2? | root cause |
|---|---|---|---|
| 1 read the exam | **1.000** | yes | binary runs as root beside the answer key (`behaviour.py:54-59`, `tests/Dockerfile:11`) |
| 2 empty + delete py | 0.333 | yes | `build`+`no_python` scored standalone (`reward.toml`) |
| 3 visible lookup | 0.491 | yes | free points + echo (visible/hidden split itself is fine) |
| 4 build-only | 0.167 | no | `build` free (`build.py`) |
| 5 echo | 0.491 | yes | behaviour partial credit has no floor + free points |

The exam leak (Cheat 1) is the one that must be closed first: it makes the whole task passable with zero porting.

## Note on line endings (reproducibility)

The target was checked out on Windows with `git core.autocrlf=true`, which rewrote his committed LF files to CRLF locally. A CRLF `test.sh` cannot run (`/bin/bash\r` not found) and CRLF answer files never match a Go port's LF output. His committed blobs are LF (his own runs pass), so each scratch copy's `*.sh` and `tests/data/*.txt` are stripped back to LF before running — this restores his real committed bytes, it does not change his task. The runners that do this are `run_attacks.ps1` and `run_reference.ps1` in this folder.
