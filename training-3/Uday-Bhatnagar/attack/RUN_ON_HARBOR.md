# Run the 3 cheats in real Harbor (Day 4, Step 4.2) — about 20 minutes

Why: the guide says every number must come from a real Harbor run with a job folder. My scores are a local preview only.

## 0. One-time setup (PowerShell, inside the class repo, in your folder)
```powershell
cd <repo>\Uday-Bhatnagar
# copy of Sneha's task. NEVER edit her original folder.
New-Item -ItemType Directory attack\target -Force | Out-Null
Copy-Item ..\SnehaSadhukhan\titlecase-go\* attack\target -Recurse -Force
```
Copy the files from this package into `attack\` (cheat1..3, TARGET.txt, ATTACK.md, results). Put `.gitignore` in `Uday-Bhatnagar\`.

**Line endings matter.** The cheats must be LF, not CRLF, or Docker shows "bad interpreter". After copying:
```powershell
foreach ($n in 1,2,3) {
  $p = "attack\cheat$n\solve.sh"
  (Get-Content -Raw $p) -replace "`r`n","`n" | Set-Content -NoNewline -Encoding utf8NoBOM $p
}
```

## 1. For each cheat N in 1, 2, 3
```powershell
$n = 1                                        # then 2, then 3
Remove-Item scratch\cheat$n -Recurse -Force -ErrorAction SilentlyContinue
Copy-Item attack\target scratch\cheat$n -Recurse
Remove-Item scratch\cheat$n\solution\* -Recurse -Force          # remove Sneha's real port
Copy-Item attack\cheat$n\solve.sh scratch\cheat$n\solution\solve.sh
harbor run -p scratch\cheat$n -a oracle
```
Harbor prints a job folder like `jobs\2026-11-19__10-12-03`. Then:
```powershell
Get-Content jobs\<that-folder>\<trial>\verifier\reward.txt    # or reward.json
Copy-Item  jobs\<that-folder>\<trial>\verifier\reward.* attack\results\cheat$n-reward.json
```
Write the reward and the job-folder name into `ATTACK.md` (the `____` blanks). If your number differs from my preview, keep **yours** and say so.

## 2. What I expect (so you can spot surprises)
| Cheat | Local preview | If Harbor differs, check |
|---|---|---|
| 1 Read the exam | 1.0 | Does the verifier container really contain `/tests/data/hidden.json`? (`tests/Dockerfile:13`) |
| 2 Python inside | 1.0 | Is `python3` on PATH in the verifier? Slow (~45 s) because of the regex shim; verifier timeout is 600 s. |
| 3 Lookup + half port | 0.0 | Needs `python3` in the agent image at solve time to add the 73 TEST_DATA pairs; if missing it just loses some, still 0. |

## 3. Push (Day 4)
```powershell
git status          # every line must be inside Uday-Bhatnagar\
git add Uday-Bhatnagar/attack Uday-Bhatnagar/.gitignore
git commit -m "attack: 3 cheats on Sneha Sadhukhan's task"
git push
```
`attack\target\` and `scratch\` are in `.gitignore`, so they will not be pushed. Then tell Sneha the report is ready.

## 4. Be ready to explain (the trainer may ask)
- Cheat 1: why the same container holding the code and the answers is the real bug.
- Cheat 2: why `instruction.md` saying "no Python" is not the same as a test enforcing it.
- Cheat 3: why 118/141 correct still gives 0.0.
