# local/titlecase-go

Port python-titlecase (MIT, commit `42f43e2`) to Go; the output must match the original
`titlecase()` byte for byte, in `re` mode (WITHOUT the `regex` package).

- Exam: `tests/data/inputs.txt` + `answers.txt`, 100,000 titles, made with `../kit/`
  (see `../HARDEN.md`).
- Grading (`tests/`, Reward Kit, weighted mean): build 1, no_python 1 (gated on ≥ 50% right),
  behaviour 4 = `(share − 0.5) / 0.5`, 0 at or below 50%.
- Separate verifier container with no network; the agent's program runs there as `nobody`
  and cannot read `/tests`. No Python in either image. Agent network: model endpoint only.
- `cheat/` and `screenshots/` are from practice 1 (before hardening).

Results after hardening: oracle 1.0, nop 0.0, every known cheat 0.1667 — see `../HARDEN.md`.
