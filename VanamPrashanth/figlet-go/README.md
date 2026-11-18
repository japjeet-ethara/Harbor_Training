# FigletForge/figlet-go

## Overview

A Harbor benchmark task to implement a byte-for-byte compatible Go port of the upstream [pyfiglet](https://github.com/pwaller/pyfiglet) project.

The task focuses on reproducing FIGlet rendering behavior accurately, including font parsing, character layout, smushing, kerning, text direction, justification, and command-line options.

The upstream repository is pinned to commit `255827efbc09d662875dad50fa0edc1e1263bf45` to ensure reproducible reference behavior.

## Repository Structure

- `environment/` — Agent environment configuration and multi-stage Alpine Dockerfile.
- `solution/` — Reference Go implementation (`FigletBuilder`, font parser, layout engine) and solution script (`solve.sh`).
- `cheat/` — Memorization baseline implementation for Cheat evaluation (`cheat/solve.sh`).
- `tests/` — Visible (2,000) and hidden (2,000) datasets, test generator (`gen.py`), Go grader (`grade.go`), test script (`test.sh`), and secret banner (`secret.b64`).
- `Reward Images/` — Verified terminal execution screenshots for Oracle, NOP, Cheat evaluations, and secret rewards.
- `instruction.md` — Agent-facing task specification with testable interface and clear constraints.
- `NOTES.md` — Upstream research, behavioral details, smushing hierarchy, and implementation notes.
- `task.toml` — Harbor task configuration (schema 1.4).

## Benchmark Rewards

- **Oracle (`harbor run -p ./figlet-go -a oracle`)**: `1.0` (Build: 1.0, No_Python: 1.0, Behaviour: 1.0; 2,000/2,000 hidden cases passed; secret banner unlocked).
- **Nop (`harbor run -p ./figlet-go -a nop`)**: `0.0` (Build: 0.0, No_Python: 0.0, Behaviour: 0.0).
- **Cheat (`harbor run -p ./figlet-go -a oracle` with `cheat/solve.sh`)**: `0.1667` (< 0.20; Build: 1.0, No_Python: 0.0, Behaviour: 0.0; no secret).

## Validation Results

| Run Type | Agent / Script | Reward Score | Criteria Breakdown |
| :--- | :--- | :--- | :--- |
| **Oracle** | `oracle` (`solution/solve.sh`) | **1.000** | `build`: 1.0, `no_python`: 1.0, `behaviour`: 1.0 |
| **NOP** | `nop` (do-nothing baseline) | **0.000** | `build`: 0.0, `no_python`: 0.0, `behaviour`: 0.0 |
| **Cheat** | `cheat/solve.sh` (visible-only memorization) | **0.167** | `build`: 1.0, `no_python`: 0.0, `behaviour`: 0.0 |

- **Visible test cases**: 2,000
- **Hidden test cases**: 2,000 (zero overlap with visible cases)

The reference implementation successfully passed all 2,000 hidden cases in Harbor Oracle evaluations, unlocking the verifier secret.

### Oracle Evaluation
![Oracle Evaluation Output](Reward%20Images/oracle.png)

### NOP Evaluation
![NOP Evaluation Output](Reward%20Images/nop.png)

### Cheat Evaluation
![Cheat Evaluation Output](Reward%20Images/cheat.png)

### Secret Unlocks
- **Task Secret ("nice port, human")**:
![Task Secret Output](Reward%20Images/oracle-test.png)

- **Page Secret ("go touch grass")**:
![Page Secret Output](Reward%20Images/go%20touch%20grass.png)

## Supported Scope

The benchmark covers the following command-line options:

`-f`, `-w`, `-j`, `-D`, `-r`, `-F`, `-s`, `-n`

Options `-c`, `-L`, `-l`, and `-i` are outside the task scope.

## Execution and Verification

The task uses a multi-stage Docker environment based on Go 1.23 Alpine (non-root user `player`, no Python in final image) and a standalone Go grader (`tests/grade.go`) executed via `tests/test.sh`. The verifier tests:
1. `build` (weight 1/6): `go build -o /tmp/figlet .` succeeds in `/workspace/repo`.
2. `no_python` (weight 1/6): No `.py` files under `/workspace/repo` AND at least one hidden case matches.
3. `behaviour` (weight 4/6): Exact stdout match ratio across 2,000 hidden test cases.
4. `secret`: Unlocks secret banner rendered with `/tmp/figlet -f slant` upon achieving 1.0 behavior score.

## Honest Lines & Challenges Hit

### Environment & Porting Challenges
- **Docker Trap & Non-root User**: `golang:1.23-bookworm` bundles Python 3 by default (violating requirement D2), while `golang:1.23-alpine` lacks `bash` out-of-the-box (breaking Harbor orchestration). Solved via a pinned multi-stage Alpine build with `apk add --no-cache bash` and non-root user `player` (UID 1000).
- **Pure Go Standard Library**: No external dependencies allowed (`golang.org/x/...`). All font parsing, smushing rules, kerning, text orientation, and terminal word-wrapping had to be written from scratch using only the standard library.
- **Cross-Platform CRLF vs. LF Trap**: Developing on Windows can cause Git to checkout shell scripts with CRLF (`\r\n`) line endings, which triggers `execve: /bin/sh^M: bad interpreter` inside Linux containers. Enforced strict `eol=lf` via `.gitattributes` for all `.sh`, `.go`, `Dockerfile`, `.b64`, and `.jsonl` files.

### Rules the Agent Kept Getting Wrong
- **Universal Smushing in RTL (`smushMode & 63 == 0`)**: Overlapping dominance depends on stream sequence. In `-D right-to-left`, the left character is rendered later and must override the right character, which agents consistently inverted.
- **Rule 5 (Big X Smushing - `SM_BIGX = 16`)**: The agent smushed both `'<'` + `'>'` and `'>'` + `'<'` into `'X'`, whereas pyfiglet/FIGlet only smushes inward brackets (`'>'` + `'<'` $\to$ `'X'`), leaving `'<'` + `'>'` unsmushed.
- **Rule 4 (Opposite Pair Smushing - `SM_PAIR = 8`)**: The agent smushed identical brackets like `[` + `[` instead of strictly opposing pairs (`[` + `]`, `{` + `}`, `(` + `)`) into `'|'`.
- **Rule 6 (Hardblank Smushing - `SM_HARDBLANK = 32`)**: The agent treated hardblanks (`$`) as normal blank spaces during kerning passes, rather than preserving them as visible sub-characters until final output sanitization.

## Secrets
- **Task Secret**: `"nice port, human"` rendered in `slant` font upon achieving 100% test completion.
- **Page Secret**: `"go touch grass"` rendered cleanly in `slant` font via `cd /workspace/repo && go build -o /tmp/figlet . && /tmp/figlet -f slant "$(echo Z28gdG91Y2ggZ3Jhc3M= | base64 -d)"`.
