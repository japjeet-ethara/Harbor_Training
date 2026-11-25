# DEFENCE.md - Koshki Raghuwanshi

## Proofs on my hardened task (run from the repo copy)
- oracle: 1.0 (jobs/2026-11-23__11-13-42)
- nop: 0.0 (jobs/2026-11-23__11-16-00)
- Tanya's cheats, each must be below 0.2:
    cheat1  reward 0.0  jobs/2026-11-23__11-17-34
    cheat2  reward 0.0  jobs/2026-11-23__11-19-19
    cheat3  reward 0.0  jobs/2026-11-23__11-21-05

## Strongest cheat against my task, before and after
Tanya's cheat 1, "Python inside": it kept the original Python titlecase, renamed every .py file to .py.txt, and shipped a tiny Go program that called python3 at run time. Before: 1.0 (jobs\2026-11-19__16-50-53). After: 0.0 (jobs/2026-11-23__11-17-34).
Why it worked: no_python only checked that no file name ended in .py, the verifier image still had Python, and behaviour only compared output.
What I changed: no_python.py rejects any file name containing ".py"; the verifier image deletes /usr/bin/python*; go_run.py hides /usr/local/bin from the submitted program; behaviour is an exact byte match on 100,000 titles; reward.toml is all-pass.
Her other two cheats: half port 0.2696 to 0.0; build trick 0.1667 to 0.0.

## Before and after exam table
| Port | Wrong on new 100,000 exam | Old 2,000 exam |
|------|---------------------------|----------------|
| my oracle | 0 | passes |
| Aahan Trikha | 3900 | passes (not caught) |
| Tanya Shrivastava | 3053 | passes (not caught) |

## A real bug the new exam found in my own port
The first time I measured my own oracle on the 100,000 titles it was wrong on 488. Examples: input 'BBC: OF at\xa0Mcx-\tif summer time by' should give 'OF' but my port gave 'Of'; input 'ocean x-ray The guide ftp://host/file or\xa0v. FOR en' should keep 'FOR' but my port gave 'For'.
Cause: the original keeps an already-uppercase small word (OF, FOR, BUT, THE) uppercase when it follows sub-phrase punctuation such as ": " or "- ". My port capitalised it as Of/For/But/The.
Fix in solution/solve.sh: added isUpperSmall and endsWithSubPunct to keep those words uppercase, added isAllUpperWord, and applySubphrase now takes allCaps and keeps all-caps words (and a v./vs. chain) as the original does. Now wrong on 0 of 100,000. I did not remove any input.

## What surprised me
My old 2,000-title exam gave a perfect score to two classmate ports that are wrong on 3,900 and 3,053 of 100,000 titles. Tanya's 3,053 is exactly the number of answers that differ between regex and non-regex mode, so her port probably follows the other mode. That is why instruction.md now says: WITHOUT regex.

## What did not work
- My first extra test (cheat 4, Tanya's cheat 1 calling /opt/rewardkit/bin/python3) scored 0.0 for the wrong reason: the filename check caught the .py.txt files first. I built cheat 4b with .dat names to test the interpreter itself; it also scored 0.0.
- The task copied into the repo would not build: docker-compose.yaml pointed to ../../python-titlecase, which does not exist there. I put the Python source in task/environment/python-titlecase-src and pointed the compose file to it, then re-ran the oracle from the repo copy: 1.0.
- My first proof script copied an old reward when Docker was not running, so nop and the cheats showed 1.0. I caught it because every job folder was the same, fixed the script to stop when no new job appears, and re-ran everything.
- All-pass is harsh: one wrong title gives 0.0, so I needed compare.py to debug my own port.
- I cannot prove there is no other cheat; I tried Tanya's three plus two Python-path variants.

## Talk plan (5 minutes)
1. Strongest cheat (Python inside), 1.0 to 0.0: what it did and the lines in no_python.py that stopped it.
2. The before/after table: 2,000 versus 100,000 titles.
3. My own 488-title bug: show one input, what it should give and what I gave.
4. The surprise: an exam can give a perfect score to a port that is wrong on thousands of titles.
Be ready to explain each changed line: git diff between my Day 4 commit and now.
