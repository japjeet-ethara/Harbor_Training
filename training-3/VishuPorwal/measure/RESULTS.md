# Evaluation Results — Go Titlecase Reference Ports

This document records the comparative measurements of three Go titlecase reference ports evaluated across two exam suites (Old: 2,000 titles; New: 100,000 titles).

## Verifier & Environment Setup

- **Hardened Verifier**: Both exams were graded using the identical hardened verifier with filesystem isolation (unprivileged execution inside a `chroot` jail with supplementary groups cleared).
- **Prerequisite Scoring Rule**: `build` and `no_python` are hard prerequisites. If either check fails, the final reward is `0.0`. If both pass, the reward equals the behavioral credit (`behaviour`).
- **Exam Suites**:
  - **Old Exam**: 2,000 titles (`hidden_inputs.txt`, `hidden_expected.txt`).
  - **New Exam**: 100,000 titles generated reproducibly and frozen twice under Python 3.14.10 in standard-library `re` mode (`0` dropped).
- **Source Artifact Status**: All six verifier artifacts (`reward.json`, `reward-details.json`, `test-stdout.txt`) were successfully located and verified; none are missing. The original verifier `reward.json` files are archived alongside this document.

---

## Comparative Summary

| Port Author | Pinned Revision | Exam Size | Harbor Job ID | Saved Reward | Exact Match Count | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Vishu Porwal** | `512aba1` | 2,000 | `063bc1c5-c2af-43fa-9150-d310612a5805` | `1.0` | Not recorded in artifact | Full credit |
| **Vishu Porwal** | `512aba1` | 100,000 | `8cd0739c-c9d9-4e6d-8aef-9fb7e60d71fa` | `1.0` | Not recorded in artifact | Full credit |
| **Nikhil Choudhary** | `a1173ff` | 2,000 | `a06ed408-7d05-411e-b8df-cf4cb8e3e744` | `0.9965` | 1,993 / 2,000 | 7 mismatches |
| **Nikhil Choudhary** | `a1173ff` | 100,000 | `df426668-ac1c-46ac-9dd9-0bfbc523db23` | `0.9602` | 96,017 / 100,000 | 3,983 mismatches (raw: 0.96017) |
| **Omar Ghyas** | `1aea2bf` | 2,000 | `fe28c343-e1a4-4085-b8da-42fa7e783099` | `1.0` | Not recorded in artifact | Full credit |
| **Omar Ghyas** | `1aea2bf` | 100,000 | `f1ce426f-97b9-4173-9146-785e991c60cd` | `0.9697` | 96,971 / 100,000 | 3,029 mismatches (raw: 0.96971) |

*Note: For evaluations saved as `1.0`, the verifier artifact does not log individual match counts or unrounded precision beyond the reported reward value.*

---

## Detailed Evaluation Records

### 1. Vishu Porwal Reference Solution
- **Pinned Revision**: `512aba1c0f0a70c960b7d2fded998276b6445310`
- **Old Exam (2,000 titles)**:
  - **Job ID**: `063bc1c5-c2af-43fa-9150-d310612a5805`
  - **Saved Reward**: `1.0` (Archived file: `vishu-old-reward.json`)
  - **Component Scores**: `build`: 1.0, `no_python`: 1.0, `behaviour`: 1.0
  - **Exact Match Count**: Not recorded in artifact
  - **Exceptions**: None (`0`)
- **New Exam (100,000 titles)**:
  - **Job ID**: `8cd0739c-c9d9-4e6d-8aef-9fb7e60d71fa`
  - **Saved Reward**: `1.0` (Archived file: `vishu-new-reward.json`)
  - **Component Scores**: `build`: 1.0, `no_python`: 1.0, `behaviour`: 1.0
  - **Exact Match Count**: Not recorded in artifact
  - **Exceptions**: None (`0`)

### 2. Nikhil Choudhary Reference Port
- **Pinned Revision**: `a1173ff2253399c1728efa4e25255b6495c51493`
- **Old Exam (2,000 titles)**:
  - **Job ID**: `a06ed408-7d05-411e-b8df-cf4cb8e3e744`
  - **Saved Reward**: `0.9965` (Archived file: `nikhil-old-reward.json`)
  - **Component Scores**: `build`: 1.0, `no_python`: 1.0, `behaviour`: 0.9965 (raw: 0.9965)
  - **Exact Match Count**: **1,993 / 2,000** (7 mismatches)
  - **Exceptions**: None (`0`)
- **New Exam (100,000 titles)**:
  - **Job ID**: `df426668-ac1c-46ac-9dd9-0bfbc523db23`
  - **Saved Reward**: `0.9602` (Archived file: `nikhil-new-reward.json`)
  - **Component Scores**: `build`: 1.0, `no_python`: 1.0, `behaviour`: 0.9602 (raw: 0.96017)
  - **Exact Match Count**: **96,017 / 100,000** (3,983 mismatches)
  - **Exceptions**: None (`0`)

### 3. Omar Ghyas Reference Port
- **Pinned Revision**: `1aea2bf3fb67c8ec034a3c9467c011c4c65e1514` (`OmarGhyas/titlecase-go/solution/solve.sh`)
- **Old Exam (2,000 titles)**:
  - **Job ID**: `fe28c343-e1a4-4085-b8da-42fa7e783099`
  - **Saved Reward**: `1.0` (Archived file: `omar-old-reward.json`)
  - **Component Scores**: `build`: 1.0, `no_python`: 1.0, `behaviour`: 1.0
  - **Exact Match Count**: Not recorded in artifact
  - **Exceptions**: None (`0`)
- **New Exam (100,000 titles)**:
  - **Job ID**: `f1ce426f-97b9-4173-9146-785e991c60cd`
  - **Saved Reward**: `0.9697` (Archived file: `omar-new-reward.json`)
  - **Component Scores**: `build`: 1.0, `no_python`: 1.0, `behaviour`: 0.9697 (raw: 0.96971)
  - **Exact Match Count**: **96,971 / 100,000** (3,029 mismatches)
  - **Exceptions**: None (`0`)

---

## Archived Reward Files

Alongside this report, the following original verifier reward files are stored in `training-3/VishuPorwal/measure/`:
- `vishu-old-reward.json`
- `vishu-new-reward.json`
- `nikhil-old-reward.json`
- `nikhil-new-reward.json`
- `omar-old-reward.json`
- `omar-new-reward.json`
