# Attack Report — Priyesh Singh's titlecase-go

**Target:** Priyesh Singh  
**Commit attacked:** `931c71ae274e9c59cf8c1354b73d81c3c9f171c1`  
**Repo:** `https://github.com/japjeet-ethara/Harbor_Training/tree/main/Priyesh%20Singh/titlecase-go`

---

## Task analysis

The agent sees: `instruction.md`, and the container at `/workspace/repo` (Python titlecase source copied in).

The verifier runs three checks (`tests/build.py`, `tests/no_python.py`, `tests/behaviour.py`), weighted 1-1-4:

| Check | File | What it tests |
|-------|------|--------------|
| `build` | `tests/build.py:9` | `go build ./...` in `/workspace/repo` returns 0 |
| `no_python` | `tests/no_python.py:10` | build passes AND no `.py` files remain under `/workspace/repo` |
| `behaviour` | `tests/behaviour.py:14` | builds binary, feeds it `/tests/data/hidden_inputs.txt`, compares output to `/tests/data/hidden_expected.txt` |

The verifier uses `environment_mode = "separate"`, so the verifier container is built from `tests/Dockerfile` (golang:1.23 + rewardkit installed via uv). The agent-built binary is copied into the verifier container and **run there**, meaning it can read any file in `/tests/data/`.

**Three weakest points:**
1. `tests/data/hidden_inputs.txt` and `tests/data/hidden_expected.txt` are stored in the same Docker image that runs the binary (`tests/Dockerfile` does `COPY . /tests/`). The binary executes inside that container and can open those paths directly. (`tests/Dockerfile:9`, `tests/behaviour.py:21`)
2. `no_python` awards its full weight (1 of 6) whenever `go build` passes and no `.py` files remain — no correctness required. (`tests/no_python.py:10`)
3. `tests/data/inputs.txt` and `tests/data/expected.txt` (the visible set) are also in the same container. Any line from the visible set that the hidden set shares gives free correct answers. (`tests/behaviour.py:9`)

---

## Cheat 1 — Runtime lookup table (hidden files)

**What it does:** Writes a Go program that, at startup, opens `/tests/data/hidden_inputs.txt` and `/tests/data/hidden_expected.txt` and builds an in-memory map. For each input line, it returns the pre-computed answer from the map; for anything not in the map it falls back to naïve per-word capitalisation. It deletes all `.py` files so `no_python` passes.

**Score:** reward **1.000** (build 1.0, no_python 1.0, behaviour 1.0)  
**Job folder:** `jobs/attack-cheat1`

**Why it worked:** The binary runs as a child process of `behaviour.py` inside the verifier container (`tests/behaviour.py:21: subprocess.run([str(BINARY)], input=HIDDEN_IN.read_bytes(), ...)`). The verifier container has both the hidden inputs and expected answers at `/tests/data/` (because `tests/Dockerfile:9: COPY . /tests/` copies all of `tests/` including `data/`). The binary therefore has read access to the exact answer sheet it is being tested against.

**How to fix:** Run the binary in a separate network-isolated container that does not contain `tests/data/`. Pass inputs via stdin and collect stdout there, then compare to the expected file from outside. Alternatively, ship only a one-way hash of the expected file inside the container and compare hashes, keeping the plaintext expected answers outside.

---

## Cheat 2 — Delete trick (build + no_python free points)

**What it does:** Deletes all `.py` files and writes a minimal Go program that only capitalises the very first character of each input line. This passes `go build ./...` and leaves no `.py` files but produces wrong output for almost every title.

**Score:** reward **0.353** (build 1.0, no_python 1.0, behaviour 0.030)  
**Job folder:** `jobs/attack-cheat2`

**Why it worked:** `build` (weight 1) and `no_python` (weight 1) together contribute 2/6 of the total reward. A completely wrong port still earns ≈0.333 from those two checks alone without any correct title-casing. The small behaviour score (0.030) comes from the few lines where capitalising the first character happens to be correct (e.g. lines starting with a capital).

**How to fix:** Make `no_python` conditional on a minimum behaviour threshold (e.g. require behaviour ≥ 0.5 before awarding `no_python`), or drop the separate `no_python` check and fold it into `behaviour` as a hard prerequisite. This way a stub that produces wrong output cannot earn free structural points.

---

## Cheat 3 — Visible-set lookup with naive fallback

**What it does:** Builds a Go program that reads `tests/data/inputs.txt` and `tests/data/expected.txt` (the **visible** set, also present in the verifier container) into a lookup map. For hidden inputs that happen to match a visible input, it returns the correct answer. For everything else it falls back to naïve per-word capitalisation.

**Score:** reward **0.482** (build 1.0, no_python 1.0, behaviour 0.223)  
**Job folder:** `jobs/attack-cheat3`

**Why it worked:** The visible `inputs.txt` (2000 lines) and the hidden `hidden_inputs.txt` (2000 lines) are drawn from the same generator with the same word pool. Some hidden lines overlap with or are similar to visible lines. The 22.3% hit rate on behaviour confirms meaningful overlap. The root cause is the same as Cheat 1: both sets are in `/tests/data/` inside the verifier container.

**How to fix:** Same fix as Cheat 1. Additionally, ensure the visible and hidden sets are drawn from non-overlapping pools (different seeds and word families), so a lookup against the visible set gives near-zero correct answers on the hidden set.

---

## Summary

| Cheat | Description | Reward |
|-------|-------------|--------|
| 1 | Runtime lookup of hidden answer files | **1.000** |
| 2 | Delete `.py` files, stub binary | 0.353 |
| 3 | Lookup visible expected answers + naive fallback | 0.482 |

**Highest score achieved: 1.0 (Cheat 1)**

The root vulnerability is that the binary under test runs inside the verifier container and can read the hidden answer files directly. A correct fix requires running the binary in a container that never sees `tests/data/`.
