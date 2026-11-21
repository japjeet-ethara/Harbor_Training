# Defence Verification Summary — `JiyaPatel/task`

## 1. Incoming Attack Summary (`NiharikaMudgal`)

- **Attacker:** Niharika Mudgal (`training-3/NiharikaMudgal/attack/ATTACK.md`)
- **Target:** Jiya Patel (`JiyaPatel/titlecase-go`)
- **Attack Vectors Tested:**
  1. **Cheat 1 (Fixture Read / Lookup):** Compiled a Go binary calling `os.ReadFile("/tests/data/expected.txt")` to echo visible expected outputs (`0.3417` pre-hardening).
  2. **Cheat 2 (Partial Heuristic Port):** Compiled a Go binary splitting lines with `strings.Fields` and applying a partial lowercase small-word map (`0.4070` pre-hardening).
  3. **Cheat 3 (Prefix Truncation):** Compiled a Go binary printing only the first 25 expected lines to exploit un-gated `zip(exp, out)` scoring (`0.3417` pre-hardening).

## 2. Re-Execution Against Hardened Task (`training-3/JiyaPatel/task`)

Each of Niharika Mudgal's unmodified cheat scripts (`cheat1/solve.sh`, `cheat2/solve.sh`, `cheat3/solve.sh`) was executed in Harbor against the hardened task (`[verifier] environment_mode = "separate"`, `105,000`-line hidden exam, cardinality enforcement, and accuracy-gated `verify.py`):

| Submission | `build` | `no_python` | `behaviour` | `reward` | Proof Artifact |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **`oracle`** | `1.0` | `1.0` | `1.0` | **`1.0000`** | `proof/oracle_reward.json` |
| **`nop`** | `0.0` | `0.0` | `0.0` | **`0.0000`** | `proof/nop_reward.json` |
| **`niharika-cheat1`** | `0.0` | `0.0` | `0.0` | **`0.0000`** | `proof/niharika-cheat1-reward.json` |
| **`niharika-cheat2`** | `0.0` | `0.0` | `0.0` | **`0.0000`** | `proof/niharika-cheat2-reward.json` |
| **`niharika-cheat3`** | `0.0` | `0.0` | `0.0` | **`0.0000`** | `proof/niharika-cheat3-reward.json` |

## 3. Why Each Attack Vector Fails

1. **Cheat 1 (`0.3417` -> `0.0000`):** Separate verifier mode (`environment_mode = "separate"`) isolates `/tests` from the agent container, and `/tests/data/expected.txt` does not exist in the verifier environment (`os.ReadFile` exits with status `1`).
2. **Cheat 2 (`0.4070` -> `0.0000`):** The naive `strings.Fields` heuristic falls far below the `0.90` behavioral floor across the `105,000`-line hidden exam, and gated scoring zeroes `build` and `no_python` when behavioral accuracy is below `0.95`.
3. **Cheat 3 (`0.3417` -> `0.0000`):** `verify.py` enforces `len(out) == len(exp)` (`105,000` lines) prior to line comparison, rejecting the 25-line prefix binary with `0.0000`.
