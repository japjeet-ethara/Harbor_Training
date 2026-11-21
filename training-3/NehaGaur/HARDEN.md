# Day 5 — Hardening Report

## 1. Cheat replay and hardening

Replayed the three attacks from Lokesh Deshwal's ATTACK.md against my task.

| Test | Hardened score |
|---|---:|
| Oracle baseline | 1.0 |
| Cheat 1 — Answer Peeking | 0.0 |
| Cheat 2 — Delete & Build | 0.0 |
| Cheat 3 — Naive Capitalizer | 0.0 |

All three cheat scores are below 0.2, and the oracle remains at 1.0.

### Changes made

- Changed the reward formula so behavior correctness gates the final reward.
- Runs candidate execution as an unprivileged UID/GID.
- Restricts access to the expected-answer file.
- Rebuilt and tested the verifier image.

## 2. Larger exam

- Inputs: 100,000
- Seed: 2026
- Answers generated twice using the kit answer-generation process.
- Stable answers retained: 100,000
- Unstable answers dropped: 0
- Environment mode: separate

The two exam files are stored in `task/tests/data/`.

## 3. Port measurements

| Port | Old exam wrong (2,000) | New exam wrong (100,000) |
|---|---:|---:|
| Lokesh Deshwal | 0 | 3,142 |
| Neha Gaur | 0 | 503 |
| Saurabh Baghel | 0 | 0 |

### Measurement reports

- `measure/lokesh-old.txt`
- `measure/lokesh-100k.txt`
- `measure/neha-old.txt`
- `measure/neha-100k.txt`
- `measure/saurabh-old.txt`
- `measure/saurabh-100k.txt`

## 4. Summary

The hardened verifier gives all three replayed cheats a score below 0.2 while preserving the oracle score of 1.0. The 100,000-input exam detected errors that were not detected by the old 2,000-input exam for the Lokesh and Neha ports.
