# Re-attack on Pragati Sharma's HARDENED titlecase-go

Target: `ethara/titlecase-go` (Pragati Sharma), hardened task at
`training-3/PragatiSharma/task` @ `b21faef9ce8116cc0af36f76c1a31aad83025304`.
Day 4 target was the same author's task before hardening.

Each cheat runs as the oracle in a scratch copy of her task, with only `solution/solve.sh`
replaced, then graded with her own `tests/grade` (Reward Kit 0.2.4). The numbers below are from Harbor 0.25.0 runs; the reward files are in `results/`.

## What her Day-5 hardening closed (and it holds)

Her three original holes are shut, and my re-attack confirms it:

- **Free build/no_python points** — `reward.toml` now pays only `behaviour`, which is 0 unless build
  and no_python both pass. The old "delete .py, build, collect 2/6" trick earns nothing.
- **Running the image's Python** — the submitted program runs as UID 40000 with `setpriv`
  (`grade/support.py`), and `tests/Dockerfile` makes `python3.12`, the libs and `/usr/local/lib/python3.12`
  root-only, with a build-time self-check that UID 40000 can run none of them. Cheat 2 from Day 4
  (`os/exec` into `python3`) now exits 1, `no python found`.
- **Reading the hidden answers** — `/tests` is root-only, the program runs from a temp dir, and the
  image build fails if UID 40000 can read `data/answers.txt`. Plus a kill-sweep and `/logs/verifier`
  at mode 700. A run-time file read of the answers is dead.

That is good, careful work. But two holes survive.

## Cheat 1 — Memorise the public graded exam  (reward 1.0)

What it does: ports nothing. `grade/behaviour/check.py` grades against `/tests/data/inputs.txt` and
`/tests/data/answers.txt`, and **those exact files are committed in the public class repo**. The cheat
downloads them (the agent room has `network_mode = "public"`), embeds `answers.txt` with `go:embed`,
and prints the answer for each input line. It obeys every hard rule: Go stdlib only (`embed` is
stdlib), no `.py` left, `go build ./...` passes.

Score (Harbor): **reward 1** — build 1.0, no_python 1.0, behaviour 1.0 (100000/100000).

Why it worked: the Day-5 fixes all assume the answers are secret — root-only `/tests`, locked Python,
`no-network` verifier, the kill sweep. None of that matters, because the answers were never secret;
they are published next to the task. Locking the room does nothing when the key is printed on the door.

How to fix: the score cannot rest only on data that ships in the repo.
- Grade partly on a **fresh exam generated at grading time** inside the verifier (new random lines from
  `kit/make_pool.py`, answered by the original Python held root-side), and take the **lower** of the
  committed-exam share and the fresh-exam share. A lookup table of the public answers then scores ~0
  on the fresh half. (This is what the hardened `AyushKhurana/task` does.)
- And shut the download route: set the **agent** phase to `network_mode = "allowlist"` with only the
  model host, so the committed answers cannot be fetched while the agent works.

## Cheat 2 — "Go standard library only" is never checked  (reward 0.116)

What it does: a weak half-port (capitalise words, keep the small words lower) that **also imports
`os/exec` and `syscall`** through a nested module wired in with `replace`. Her grader
(`grade/build`, `grade/no_python`, `grade/behaviour`) only checks that the build succeeds and no `.py`
remains. It never inspects imports, so forbidden packages, a nested module, or a vendored third-party
module all pass.

Score (Harbor): **reward 0.1159** — build 1.0, no_python 1.0, behaviour 0.1159 (11592/100000).
The 0.116 is just the half-port's partial credit; the finding is that the imports pass at all.

Why it worked: `instruction.md` hard rule 1 says "Use only the Go standard library", but nothing in the
grader enforces it. This is the same escape-hatch family that a `no_exec` gate closes, and her grader
has no such gate. On this task it does not lift the score on its own (the answers are the real win), but
it means the "stdlib only" and "no spawning other programs" expectations are unguarded — a submission
could shell out to `perl`/`sh`/`bash` (available to UID 40000) or vendor a pure-Go interpreter.

How to fix: add a `no_exec`-style check that runs `go list -deps -json ./...` over the whole build and
fails on `os/exec`, `syscall`, `unsafe`, any nested `go.mod`/`go.work`, any non-main module in the
closure, and any cgo/assembly/C file; and scan `.go` sources for `os.StartProcess` and `go:linkname`.

## Honest notes

- Cheat 1 is exactly the hole Pragati's own `HARDEN.md` lists under "Remaining limitations #1"
  ("A program can embed `answers.txt` as a lookup table … score 1.0 … This was not run as a test").
  The re-attack confirms it runs, at 1.0, against the committed grader.
- Her SOP requires the exam to be committed, so she could not simply hide it; the fix is a fresh
  grade-time exam, not a secret file.
- Everything her hardening targeted stays closed. These two are what is left.
