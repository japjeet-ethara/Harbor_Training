# Practice Task 2 — figlet-go (Ayush Khurana)

Port of **pyfiglet 1.0.4** (`pwaller/pyfiglet`, commit `255827efbc09d662875dad50fa0edc1e1263bf45`, 2026-08-02, MIT) to a Go 1.23 standard-library-only program, graded by Harbor 0.25.0.

The task is in [`figlet-go/`](figlet-go/). Notes on the original (licence, the missing-fonts failure and its fix, the six smushing rules with examples, the eight options, rare cases) are in [`NOTES.md`](NOTES.md).

## Results (real Harbor runs on my machine, `results/`)

| Run | behaviour | build | no_python | **reward** | secret |
|---|---|---|---|---|---|
| oracle | 1.000 | 1.000 | 1.000 | **1.000** | drawn (`ported by khurana`) |
| nop | 0.000 | 0.000 | 0.000 | **0.000** | no |
| cheat (memorised visible answers) | 0.000 | 1.000 | 0.000 | **0.167** | "No secret for you. Yet." |

Files: `results/{oracle,nop,cheat}.{result.json,reward.json,verifier-log.txt}`.
The page's own secret (Step 8) came out clean from the oracle's Go code in the built image.

Six more cheat attempts, run through the real grader in the same image (`figlet-go/dev/try_verifier.sh`, output in `results/extra-cheats.txt`): build-only, echo the arguments, read the hidden answers from `/tests` at run time, run Python through `os/exec`, fetch the answer over `net/http`, an assembly stub. Every one scores **0.1667** (build only). The last three are stopped by the hard rules before they are run.

## What is in the task

| Step | File | Notes |
|---|---|---|
| 2 | `environment/Dockerfile`, `task.toml` | two stages (`alpine:3.20` fetches pyfiglet at the pinned commit and does the Makefile font step; `golang:1.23-alpine` is the room), both pinned by digest; `bash`; user `player` (uid 1000) owns `/workspace/repo`; no Python (`NO_PYTHON` verified); `[agent] user = "player"`, `network_mode = "public"`, shared verifier |
| 3 | `instruction.md` | every sentence is checked by the grader; no test names, no answers, no secret |
| 4 | `tests/gen.py`, `tests/data/{visible,hidden}.jsonl` | seeded (`random.Random(7)`), every `out` comes from the original `main()`; 2000 + 2000 cases with no shared argument list; byte-identical on a second run and on a different Python (3.10 and 3.13) |
| 5 | `tests/grade.go`, `tests/test.sh`, `tests/secret.b64` | Go standard library only; weights **1 / 1 / 4** as the page asks |
| 6 | `solution/solve.sh` | Go port written line by line from `FigletBuilder`; fonts embedded with `go:embed`; `.py` files deleted |
| 7 | `cheat/solve.sh` | memorises `visible.jsonl`, obeys every hard rule |
| — | `dev/` | `showdiff.go` (first differing cases), `fuzz.py`, `try_verifier.sh`, `pin_digests.sh`, `make_solve.py`, `make_cheat.py`, `oracle/main.go`, `extra-cheats/` |

## Evidence that the exam is right

- Oracle: 2000/2000 visible and 2000/2000 hidden identical to the original. 20,000 extra random cases over all 72 fonts: 0 differences (`dev/fuzz.py`).
- 300 hidden cases re-run through the real `python -m pyfiglet` command line: 0 differences from the stored `out`.
- The cheats work when the defences are off (the memorising cheat answers 2000/2000 visible cases; the "read /tests" cheat answers 50/50 hidden cases when it is allowed to read) and fail under the real grader.

## Where I went beyond the page (all three are additive; an honest solution still scores 1.0)

1. `no_python` and the "hard rules" are enforced as source facts, not only "no `.py`": no `os/exec`, `syscall`, `unsafe`, `plugin`, `net` (also through dependencies, e.g. `net/http`), no cgo / assembly / C files, no `go:linkname`, no third-party packages. `instruction.md` states every one of these.
2. A program that breaks a hard rule is **not run**, so it cannot earn behaviour points. Without this, a Go wrapper that runs a downloaded Python would score 5/6 (the room has public network at agent time).
3. `[verifier] user = "root"`: the grader keeps `/tests` root-only and runs the program under test as `nobody`, from an empty working directory, with a minimal environment. Harbor's default would run the verifier as the image's last `USER` (`player`), the same user that built the program.

The reward formula itself is exactly the page's: `(1*build + 1*no_python + 4*behaviour) / 6`, and the secret needs behaviour 1.0 plus the hard rules.

## The two lines

- **Smushing rule:** not measured yet. I have not run a free Cursor agent on `instruction.md`, so I cannot say which rule broke an agent most; I will add that line after a real attempt. What I expect to trip a port, from reading the original: the hierarchy rule, because Python's `'' in '|'` is `True` (an empty left character can trigger it), followed by `-s` silently beating `-n`. My own port had one slip, caught by reading before the first run (the header field for the old layout is `header[4]`, not `[3]`).
- **Docker/Harbor traps I actually hit:** (1) `go build ./...` on a single main package writes a binary into the repository, so the oracle and the grader send it to a scratch folder with `-o dir/`; (2) the shared verifier runs as the image's last `USER`, hence `[verifier] user = "root"`; (3) `docker inspect ... RepoDigests` gave nothing on this Docker version, so `pin_digests.sh` reads the `Digest:` line of `docker pull`. The traps the page warns about (bookworm has Python, Alpine has no bash) are avoided by construction and checked: `NO_PYTHON`, `/bin/bash`.

## Reproduce

```
git clone https://github.com/pwaller/pyfiglet && cd pyfiglet && git checkout 255827efbc09d662875dad50fa0edc1e1263bf45
mkdir -p pyfiglet/fonts && cp pyfiglet/fonts-standard/* pyfiglet/fonts/ && cd ..
python3 figlet-go/tests/gen.py          # same two .jsonl files (sha256 in NOTES.md)
harbor run -p ./figlet-go -a oracle     # 1.0
harbor run -p ./figlet-go -a nop        # 0.0
# copy cheat/solve.sh over solution/solve.sh, run the oracle command, put the real one back (sha256 fedeb39f...)
```
