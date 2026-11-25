# DEFENCE.md — Day 6 Notes for 5-Minute Talk

Presenter: Shashwat Suman  
Task: `titlecase-go` porting  
Attacker: Ansh Dixit  

---

## 1. Strongest Cheat Against My Task & Score Changes

- **Strongest Cheat:** **Cheat 1 ("Read the Exam at Run Time")** & **Cheat 2 ("Python inside")**
  - **Before Hardening:** Both scored a full **1.000000** (reward 1.0, build 1.0, no_python 1.0, behaviour 1.0).
  - **After Hardening:**
    - Cheat 1 scored **0.000000** (completely blocked from accessing test answer keys).
    - Cheat 2 scored **0.012195** (caught by `no_python.py` inspecting file contents and blocking `os/exec` subprocesses).
    - Cheat 3 (empty stub) dropped from **0.333333** to **0.024390** due to reweighted scoring in `reward.toml`.
  - Every attacker cheat now scores strictly **below 0.20**.

---

## 2. Before and After Exam Table

| Port | Old Exam (2,000) | New Exam (100,000) | Mode Tested | Chance 2K Misses |
| :--- | :--- | :--- | :--- | :--- |
| **my-oracle** | 1.0 (0 wrong) | 0 wrong | WITH regex | 100% |
| **RamandeepSingh** | 1.0 (0 wrong) | 0 wrong | WITH regex | 100% |
| **VishuPorwal** | 1.0 (0 wrong) | 3,053 wrong | WITHOUT regex | 0% |
| **AmanEthara** | 1.0 (0 wrong) | 2,543 wrong | Mixed/regex diffs | 0% |

### Key takeaways:
- Vishu's port passed the old 2,000 test suite because the old suite lacked the edge cases that differentiate Python's standard `re` from the `regex` module. On the 100,000-input suite, 3,053 differences emerged immediately (`v1.2`, quotation marks, and Unicode words).
- Aman's port failed 2,543 cases on rare subphrase and dotted constructs.

---

## 3. What Surprised Me

- **The fragility of container-local execution**: Even when setting `environment_mode = "separate"` in `task.toml`, the verifier runs the student's compiled executable inside its *own* grading container. If `/tests/data/` is world-readable, the binary can simply read the answers directly. Sandboxing the binary into `/tmp/run_sandbox`, restricting directory permissions, and hashing expected answers in memory before evaluation was essential to close the hole completely.
- **How 100,000 inputs expose mode divergence**: The exact 3,053 difference figure described in the training guide appeared in our real test run on Vishu's port, proving that stating the specification mode (`WITH regex` in `instruction.md`) is critical for accurate grading.
