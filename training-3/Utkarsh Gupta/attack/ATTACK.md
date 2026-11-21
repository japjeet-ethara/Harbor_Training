# Attack Report — KeshavKumar's titlecase-go task

Target: KeshavKumar  
Commit attacked: f8641edad51eb78873463cc7171d0666a8c8cae9  
Attacker: Utkarsh Gupta

---

## Cheat 1 — Read the exam (lookup table from hidden files)

**What it does:**  
Writes a Go binary that opens `/tests/data/hidden_inputs.txt` and
`/tests/data/hidden_expected.txt` at startup, builds an in-memory map of
input → expected, then answers every stdin line from that map. The idea was
that the verifier runs in a "separate" container where `/tests` is mounted, so
the hidden answers would be readable at runtime.

**Score:** reward 0.1667 (build 1.0, no_python 0.0, behaviour 0.0)  
**Job folder:** `jobs/2026-11-20__15-00-55`

**Why it failed:**  
The `/tests` mount is only present in the **verifier** container, not in the
**agent** container where `solve.sh` runs. The binary executes inside the agent
container (`/workspace/repo`), so `/tests/data/hidden_inputs.txt` does not
exist there at runtime. `loadLookup()` returns an empty map, the binary echoes
every input unchanged, and all 2000 hidden lines fail.
(tests/common.py line 19: `HIDDEN_INPUTS = DATA_DIR / "hidden_inputs.txt"` —
this path is only in the verifier image, not the agent image.)

**How to fix:**  
No fix needed from the task owner — the separation of agent and verifier
containers is exactly the right defence. The hidden data is structurally
inaccessible to the agent.

---

## Cheat 2 — Half port (simple capitalize + small-words only)

**What it does:**  
Writes a real but deliberately incomplete Go port. It capitalizes the first
letter of every word (using `unicode.ToUpper`) and lowercases the 20 small
words (a, an, and, as, at, but, by, en, for, if, in, of, on, or, the, to, v,
v., via, vs, vs.), always capitalizing the first and last word. All other
titlecase rules are skipped: Mc/Mac names, d'/o'/l' names, inline-period
detection, all-caps detection, hyphen/slash splitting, subphrase-after-colon,
UC-elsewhere, and acronym detection.

**Score:** reward 0.3233 (build 1.0, no_python 0.0, behaviour 0.235)  
**Job folder:** `jobs/2026-11-20__15-40-34`

**Why it worked partially:**  
23.5% of the 2000 hidden lines matched exactly — those are the lines where the
only rules needed are basic capitalisation and small-word lowercasing. The other
76.5% failed because the missing rules (Mc names, hyphenated words, inline
periods, etc.) produce wrong output.

**Why no_python stayed 0:**  
`tests/no_python/check.py` line 19 (`NO_PYTHON_MIN_BEHAVIOUR = 0.5`) gates the
no_python point behind ≥50% behaviour. At 23.5% the gate is not passed.

**How to fix:**  
The no_python gate already blocks this. For behaviour, the exam needs more
inputs that exercise Mc/Mac names, hyphenated words, and inline periods to push
even a half-port below the 50% threshold and ensure no partial credit leaks.

---

## Cheat 3 — Build trick (empty program, delete .py files)

**What it does:**  
Writes the absolute minimum valid Go program: a `go.mod` and a `main.go` with
an empty `main()` function that compiles but produces no output. Then deletes
all `.py` files. Tests whether the build check alone gives points, and whether
no_python fires without the 50% behaviour gate being met.

**Score:** reward 0.1667 (build 1.0, no_python 0.0, behaviour 0.0)  
**Job folder:** `jobs/2026-11-20__15-47-11`

**Why it worked partially:**  
`build` scored 1.0 — the check (`tests/build/check.py`) only verifies that
`go.mod` has no `require` directives and `go build ./...` succeeds. An empty
program satisfies both.

**Why no_python stayed 0:**  
Same gate as cheat 2 — behaviour is 0.0, well below the 0.5 threshold in
`tests/no_python/check.py` line 19.

**How to fix:**  
The no_python gate is working correctly. The only remaining risk is that build
(weight 1/6) gives 0.1667 for free. To close this, the build check could
require the binary to actually produce at least one correct output line, but
that would merge it with behaviour. The current design is intentional and
reasonable — 0.1667 is negligible credit.

---

## Summary

| Cheat | build | no_python | behaviour | reward |
|-------|-------|-----------|-----------|--------|
| 1 — Lookup table (read hidden files) | 1.0 | 0.0 | 0.0 | 0.1667 |
| 2 — Half port (simple rules only)    | 1.0 | 0.0 | 0.235 | 0.3233 |
| 3 — Build trick (empty program)      | 1.0 | 0.0 | 0.0 | 0.1667 |

**Highest score: 0.3233 (Cheat 2)**

The exam's main strength is the `NO_PYTHON_MIN_BEHAVIOUR = 0.5` gate
(`tests/no_python/check.py` line 19) which prevents cheap tricks from earning
the no_python point. The weakest point is that the behaviour score for a
half-port (23.5%) reveals the hidden test set does not have enough coverage of
the complex rules (Mc names, hyphenated words, inline periods) to push even a
lazy port below 50%.
