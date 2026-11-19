# Project audit — Ayush Ranjan

## Repository
- Remote: `https://github.com/japjeet-ethara/Harbor_Training.git`
- Branch: `training-3` tracking `origin/training-3`
- Latest fetched head at audit update: `1e90188` (the remote may advance between fetches)
- Work is confined to `training-3/AyushRanjan/`.

## Existing task and preservation
- Practice task source: repository root `AyushRanjan-titlecase-go/`.
- Personal copy: `training-3/AyushRanjan/task/`.
- Source and copy were compared by relative file path and SHA-256; all 39 files matched at copy time. The original root task remains unchanged.
- Task: port Python `titlecase` behavior to Go, reading one title per line from stdin and writing one result per line.
- Evaluation weights: build 1, no_python 1, behaviour 4 (weighted mean).
- First baseline job `jobs/ayush-day5-baseline-oracle` (result ID `77f76ae4-31ce-47db-a5d4-8c0cd83b84a8`) failed before scoring because the Windows checkout converted the test runner shebang to CRLF. Added `.gitattributes` under the personal folder to pin `task/tests/test.sh` to LF.
- The follow-up oracle run `jobs/ayush-day4-baseline-oracle-lf` (result ID `7d91e623-5b62-4d3c-9a9c-6b4e26b80072`, trial `task__gxvtsbv`) completed at `1.0`.

## Tools and prerequisites
- Harbor 0.25.0; built-in `oracle` and `nop` agents are listed.
- Docker CLI/engine 29.9.2 is available with elevated process access.
- Go is not installed on the host; Harbor task containers provide Go.
- Python 3.14.10 and uv 0.13.7 are available.
- Trainer kit scripts `make_pool.py`, `answers.py`, and `compare.py` were not found in this checkout or the attached guide.

## Pairing and available materials
- Day 4 target per supplied instructions: Akul Malviya, `AkulMalviya/titlecase-go/`.
- Target commit attacked: `528c84e137b3740c4e710ace7fcbc1866b515d3d`; Akul's task has no changes between that commit and the latest fetched branch head.
- Day 5 attacker per supplied instructions: Nitin Ethara. `training-3/NitinEthara/attack/ATTACK.md` is absent from the latest fetched `origin/training-3`.
- Before setup, `training-3/AyushRanjan/` did not exist. It now contains the preserved task copy, ignore/line-ending rules, and audit.

## Day 4 execution status
- Three final Harbor oracle runs completed; all returned reward `0.0`. See `attack/ATTACK.md` and Harbor-generated JSONs in `attack/results/`.
- The runtime lookup cheat successfully read all hidden inputs and answers. The target's committed CRLF expected data and raw-line comparison mask this behavior as a zero score.
- The attempted Python wrapper failed to import `titlecase`; it did not prove a successful Python bypass.

## Next actions
1. Obtain Nitin's missing attack report and three cheats, rerun them on the personal task, and harden against those measured issues.
2. Locate the trainer kit scripts before generating the 100K exam; do not substitute invented scripts.
