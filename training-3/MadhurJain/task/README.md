# Madhur Jain — titlecase-go (hardened)

Port python-titlecase (commit 42f43e2de55bf003b286c6f8e8d8b2d26676a167, MIT) to Go. Hardened on Day 5 of the break-and-harden training.

- Exam: 100,000 titles from `../kit/make_pool.py` (count 100000, seed 1). Answers frozen twice by `../kit/answers.py` from titlecase WITHOUT regex (re mode, Python 3.14); see `../kit/report.txt`. Stored in `tests/data/inputs.txt` and `tests/data/answers.txt`.
- Grading (`tests/checks/`): build 1 (standard library only, `go build ./...`), no_python 1 (no `.py` left, paid only when behaviour earns points), behaviour 4 (share of titles right, nothing below 90%, linear to 1.0 at 100%).
- The program is built with `CGO_ENABLED=0` and run alone in an empty chroot as user nobody, so it cannot reach Python, `/tests` or `/solution`.
- Proofs are in `../proof/`, the before-and-after report in `../HARDEN.md`.
