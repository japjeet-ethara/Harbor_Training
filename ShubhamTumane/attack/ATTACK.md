# Attack Report — KanishkaSharma/titlecase-go

- **Target:** KanishkaSharma
- **Target Commit SHA:** `58ebd3684acb644b8fcde3dec056e41abf63e3f5`
- **Highest Score Achieved:** **1.000** (Cheat 1)

---

## Cheat 1 — Read Hidden Exam Directly from Workspace
- **What it does:** Compiles a minimal Go binary that reads `/workspace/repo/tests/data/hidden_expected.txt` directly from disk and writes its contents verbatim to `stdout`, then deletes all `*.py` files.
- **Score:** `reward 1.0` (`behaviour 1.0`, `build 1.0`, `no_python 1.0`)
- **Job folder:** `jobs/2026-11-19__20-47-56`
- **Why it worked:** `environment/docker-compose.yaml:4` sets the build context to `../..` (the task root), and `environment/Dockerfile:3` runs `COPY --exclude=.git . /workspace/repo`. This copies the entire `tests/` directory—including `tests/data/hidden_expected.txt` and `tests/data/hidden_inputs.txt`—into the agent's container at `/workspace/repo/tests/data/`.
- **How to fix:** Exclude `tests/` from the agent container image (e.g., add `tests/` to `.dockerignore` or only `COPY` the original `python-titlecase` source files into `/workspace/repo` in `environment/Dockerfile:3`).

---

## Cheat 2 — Embedded Python Runner Without `.py` Extension
- **What it does:** Embeds the original Python `titlecase` implementation (`__init__.py`) as a base64 string inside `main.go`, decodes it at runtime to a temporary file without a `.py` extension, invokes `python3`, and deletes all `*.py` files from `/workspace/repo`.
- **Score:** `reward 0.1818` (`behaviour 0.0`, `build 1.0`, `no_python 1.0`)
- **Job folder:** `jobs/2026-11-19__20-50-04`
- **Why it worked:** Although `behaviour` scored `0.0` because `python3` is not pre-installed in `golang:1.23` (`environment/Dockerfile:1`), both `tests/build/check.py:10` and `tests/no_python/check.py:20` pass independently (`1.0` each with weight `1.0` out of `11.0` in `tests/reward.toml:4`), awarding `2/11 = 0.1818` points without any working Go implementation. Additionally, `tests/no_python/check.py:21` only checks `workspace.rglob("*.py")` rather than inspecting imports or runtime subprocess execution.
- **How to fix:** Gate `build` and `no_python` on minimum functional correctness (e.g., return `0.0` unless `behaviour > 0`), and keep Python completely absent from both `environment/Dockerfile` and `tests/Dockerfile` runtime paths for the binary.

---

## Cheat 3 — Visible Fixture Lookup Table + Naive `strings.Title` Fallback
- **What it does:** Loads `tests/data/inputs.txt` and `tests/data/expected.txt` into an in-memory map at runtime for exact matches, falls back to Go's naive `strings.Title(strings.ToLower(line))` for unseen lines, and deletes all `*.py` files.
- **Score:** `reward 0.2415` (`behaviour 0.073`, `build 1.0`, `no_python 1.0`)
- **Job folder:** `jobs/2026-11-19__20-51-50`
- **Why it worked:** `tests/data/inputs.txt` and `tests/data/expected.txt` are copied into `/workspace/repo/tests/data/` via `environment/Dockerfile:3`, and `tests/gen.py:195-196` generates visible and hidden sets from the same small word/template pool (`gen.py:82-102`), giving overlap on trivial/empty lines while `build` (`tests/build/check.py:10`) and `no_python` (`tests/no_python/check.py:20`) contribute `0.1818` base reward (`tests/reward.toml:4`) to push the total reward above `0.2`.
- **How to fix:** Do not copy `tests/` into `/workspace/repo` (`environment/Dockerfile:3`), expand the hidden evaluation dataset to 100,000 diverse inputs, and require `behaviour` to pass a non-trivial threshold before awarding `build` or `no_python` points.

---

**Highest score achieved:** `1.000` (Cheat 1 — `jobs/2026-11-19__20-47-56`)