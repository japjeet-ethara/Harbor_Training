# Attack Report — Target: Ansh Dixit (`anshtask1/titlecase-go`)

- **Target:** Ansh Dixit (`anshtask1/titlecase-go`)
- **Commit SHA:** `8a12385d0284da21ba6478497c37ed3bd630db16`
- **Attacker:** Jiya Patel (`JiyaPatel`)

---

## 1. Summary of Results

| Run | Strategy | Job Folder | `build` | `no_python` | `behaviour` | Total `reward` |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: |
| **Cheat 1** | Empty `func main() {}` stub + delete `*.py` | `jobs/2026-11-19__05-17-07` | `1.000` | `1.000` | `0.000` | **0.3333** |
| **Cheat 2** | 25-line naive space-split + small-word map (no regex) | `jobs/2026-11-19__05-25-50` | `1.000` | `1.000` | `0.1470` | **0.4313** |
| **Cheat 3** | `os.StartProcess` import-filter bypass + naive fallback | `jobs/2026-11-19__05-29-30` | `1.000` | `0.000` | `0.1065` | **0.2377** |

All three non-conforming solutions exceed `0.20` reward (reaching up to **0.4313**) without porting `python-titlecase`'s regular-expression rules.

---

## 2. Three Exploited Weaknesses (with Exact `file:line` Citations)

### Weakness 1: Unconditional Partial Credit on `build` and `no_python` (33.3% Free Reward)
- **Job Folder:** `jobs/2026-11-19__05-17-07` (`reward = 0.3333`)
- **Locations:**
  - `tests/build.py:11-12` (`build_all() and build_binary("/tmp/build_check_bin")`)
  - `tests/no_python.py:18-30` (`no_python` returns `True` whenever `*.py` files are absent, `go build` succeeds, `go.mod` has no `require`/`replace`, and no `*.go` file contains `"os/exec"` or `"plugin"`)
  - `tests/reward.toml:5` (`weights = { build = 1.0, no_python = 1.0, behaviour = 4.0 }`)
- **What it does & why it worked (`attack/cheat1/solve.sh`):**
  Deletes all `.py` files and writes a 3-line empty `package main; func main() {}` program. Because `build` and `no_python` are un-gated by any behavioral check and carry 1/6 weight each, the empty binary earns **`0.3333`** (`2.0 / 6.0`) while producing zero output (`behaviour = 0.000`).

### Weakness 2: Over-Weighted Simple Word Pools in `gen.py` + Line-Exact Partial Credit
- **Job Folder:** `jobs/2026-11-19__05-25-50` (`reward = 0.4313`)
- **Locations:**
  - `tests/gen.py:48-49` (`POOLS = [SMALL, NORMAL, NORMAL, NORMAL, ...]`, tripling the weight of basic lowercase dictionary words)
  - `tests/behaviour.py:23-24` (`good = sum(1 for i, e in enumerate(expected) if i < len(got) and got[i] == e); return good / len(expected)`)
- **What it does & why it worked (`attack/cheat2/solve.sh`):**
  A 25-line Go program using `strings.Split(line, " ")`, a hardcoded 21-word `small` map, and `unicode.ToUpper` on the first letter of non-small words—with **zero** regular expressions, **zero** handling of `Mc`/`Mac`, apostrophes, inline periods/URLs, acronyms, hyphens, slashes, subphrase colons, or ALL-CAPS—matches **14.70%** of hidden lines byte-for-byte (`294 / 2000`), pushing total reward to **`0.4313`**.

### Weakness 3: Naive String-Regex Import Filter in `no_python.py`
- **Job Folder:** `jobs/2026-11-19__05-29-30` (`reward = 0.2377`)
- **Locations:**
  - `tests/no_python.py:14` (`FORBIDDEN_IMPORT = re.compile(r'"(os/exec|plugin)"')`)
  - `tests/no_python.py:27-29` (`if FORBIDDEN_IMPORT.search(f.read_text(errors="replace")): return False`)
- **What it does & why it worked (`attack/cheat3/solve.sh`):**
  The regex only checks for literal `"os/exec"` and `"plugin"` strings in `.go` files. Using `"os"` with `os.StartProcess` (or `"syscall"` with `syscall.Exec`, or CGo `system()`) bypasses the static import check completely. In `cheat3`, embedding `titlecase/__init__.py` as `tc_embedded.py` tripped the `.py` extension check (`no_python = 0.0`), yet the un-gated `build` check (`1.0`) plus a 10-line word-capitalizing fallback (`behaviour = 0.1065`) still achieved **`0.2377`** (and renaming the embedded asset to `.txt` passes `no_python = 1.0` for **`0.4043`**).

---

## 3. Recommended Fixes for Hardening

1. **Gate `build` and `no_python` on minimum behavior (or use thresholded/multiplicative scoring):** Require `behaviour >= 0.95` before awarding `build` and `no_python` points (or fold `no_python` into a hard gate that zeroes out the final reward if violated) so empty or naive stubs receive `0.0`.
2. **Harden static & AST inspection in `no_python.py`:** Parse Go AST imports (`go list -json ./...`) instead of raw regexes, and forbid `os/exec`, `plugin`, `syscall`, `unsafe`, `C` (CGo), and `os.StartProcess` references, as well as hidden `.py` payloads inside non-`.py` assets (`//go:embed`).
3. **Expand and rebalance `gen.py`:** Increase the pool size (e.g., 10,000+ lines) and ensure every single line exercises at least one regex-specific edge case (`Mc`/`Mac`, `d'Artagnan`/`o'brien's`, `v1.2`/`example.com`, `state-of-the-art`/`of-the`, `TCP/IP`/`and/or`, subphrase punctuation, ALL-CAPS acronyms, and mixed whitespace) so naive space-splitting scores near `0.0`.
