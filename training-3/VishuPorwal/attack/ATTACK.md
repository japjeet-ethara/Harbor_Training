# Attack Report: Nikhil Choudhary — titlecase-go

**Target:** Nikhil Choudhary’s `titlecase-go` task

**Target Git Commit:** `a1173ff2253399c1728efa4e25255b6495c51493`

---

## Verified Controls

Verified controls for revision `a1173ff2253399c1728efa4e25255b6495c51493`:

- **Oracle:** `1.000`, Harbor job ID `671a7397-b8e5-4439-8403-01d726600eb6`
- **Nop:** `0.000`, Harbor job ID `6bcb8e20-549d-42a4-9b94-1b5a6f82c3c6`

---

## Day 4 Evidence Gap

- Nikhil confirmed the ZIP is his full set of records for the submitted task folder.
- We checked all five archived trial configs and lock files. None records a Git commit, and none of their task digests matches the digest Nikhil supplied for `a1173ff2253399c1728efa4e25255b6495c51493`.
- Trial `titlecase-go__Ds2Qj9F` (Harbor job ID `b5c5ce87-c293-45a9-a2b4-f3437000e8c9`) scored `0.000` after setup failed, before behavioral grading.

---

## Evaluation Findings

### Structural credit with zero correct outputs
- **Location:** `tests/grade.py:118–120`
- **Finding:** A reward of `0.3333` is calculated when both structural checks pass (`build = 1.0` and `no_python = 1.0`) and behavior is zero (`behaviour = 0.0`):
  ```python
  total_weight = 1.0 + 1.0 + 4.0
  final_reward = (1.0 * build_score + 1.0 * no_python_score + 4.0 * behaviour_score) / total_weight
  final_reward = round(final_reward, 4)
  ```
  `(1.0 * 1.0 + 1.0 * 1.0 + 4.0 * 0.0) / 6.0 = 2.0 / 6.0 = 0.3333`.
- **Recommendation:** Make those checks prerequisites for behavioral credit so that no credit is awarded unless behavioral checks pass.

### Execution of existing or arbitrary binary
- **Location:** `tests/grade.py:63, 69, and 81`
- **Finding:** The grading script checks for an existing `titlecase` binary in `repo_dir` (line 63) or scans for any ELF executable in the repository (line 69) and runs it, only building via `go build -o /tmp/titlecase .` if no binary is found (line 81).
- **Recommendation:** Run only the executable produced by a fresh verifier build.

### Permissive execution and comparison logic
- **Location:** `tests/grade.py:104 and the comparison loop below it`
- **Finding:** The grading script splits output into lines via `actual_lines = run_proc.stdout.splitlines()` (line 104) and loops across `min(len(actual_lines), total)`. It does not require a zero exit status from the binary, does not check that output length matches the input line count, and compares text strings rather than exact bytes.
- **Recommendation:** Require a successful exit and exactly one output record per input. Compare output records as bytes.

---

## Day 4 Evaluation Results

- **Cheat 1:** Pending
- **Cheat 2:** Pending
- **Cheat 3:** Pending
