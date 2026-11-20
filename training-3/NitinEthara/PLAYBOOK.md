# Nitin Ethara — Day 5 task handoff

## Identity and push constraints

- Commit identity: `Nitin <nitin@ethara.ai>`.
- Keep all work under `training-3/NitinEthara/`.
- Push only to the `training-3` branch. Do not push to the default branch and do not open a pull request.
- Use an explicit identity for commits:

  ```powershell
  git -c user.name=Nitin -c user.email=nitin@ethara.ai commit ...
  ```

## Repository and task

- Repository: `C:\Users\Nitin\Desktop\atk\Nitin`
- Remote: `https://github.com/japjeet-ethara/Harbor_Training.git`
- Branch: `training-3`
- Original task: `NitinEthara/titlecase-go/` (leave unchanged)
- Day 5 working copy: `training-3/NitinEthara/task/`
- Ayush Day 4 attack: `training-3/NitinEthara/attack/`
- Attacker report: `training-3/AdarshSahani/attack/ATTACK.md` (read-only)
- Official assignment: `C:\Users\Nitin\Downloads\06-break-and-harden.md`

The local branch may need a fast-forward from `origin/training-3` before committing.
Review the worktree and confirm the Nitin deliverables are the only staged files before
committing or pushing.

## Day 5 work and evidence

- The task copy was tested against all four reported cheats before hardening; actual Harbor
  reward and detail JSON files are in `measure/attacker-reruns/`.
- The exam has 100,000 stable cases, generated with seed 1 in `regex` mode. The frozen
  inputs and answers are in `task/tests/data/`; the original task remains unchanged.
- `tests/quality.py` gates structural reward on an exact pass of the complete exam.
- `measure/` records the oracle and two classmate-port comparisons. The full generated
  pool, key, job folders, scratch copies, and measured port sources are local-only and
  excluded by `.gitignore`.
- Add post-hardening Harbor reward files and the verified scores to `HARDEN.md` before
  committing. Do not claim a cheat is closed unless its post-hardening Harbor reward is
  below 0.2.
- Cheat 4 is a valid, complete Go port. If it still passes, report that accurately rather
  than penalizing a correct implementation.

## Environment notes

- Harbor: `C:\Users\Nitin\AppData\Local\Programs\Python\Python312\Scripts\harbor.exe`
- Harbor jobs must use fresh scratch copies of `task/`; normalize copied text files to LF
  before running to avoid Windows line-ending failures.
- Keep Harbor logs and generated files under ignored `jobs/` or `scratch/` directories.
- Run the Nitin oracle and no-op checks as additional validation; the expected rewards are
  1.0 and 0.0 respectively.

## Day 6 status

- `proof/` contains the oracle, no-op, and four cheat reward JSONs from Harbor runs against
  the hardened task. Cheats 1–3 are below 0.2; the complete Cheat 4 port is 1.0.
- `DEFENCE.md` summarizes the proof scores and old/new exam comparisons.
- Adarsh's independent re-attack entry still needs to be added by Adarsh to his own
  `attack/ATTACK.md`; do not edit another trainee's folder.
