# Day 6 — Defence

## Strongest attack and hardening result

Adarsh Sahani's Cheat 4 is a complete Go port that reproduces the reference behavior.
It scored 1.0 before and after hardening because it is a valid solution. The next strongest
before-hardening cheat was Cheat 3 at 0.5357. After hardening, Cheats 1–3 scored 0.0096,
0.0606, and 0.0979. Their build and no-Python checks now require an exact pass of all
100,000 frozen cases, removing structural credit for incomplete solutions.

| Run | Before reward | After reward |
| --- | ---: | ---: |
| Oracle | not run before hardening | 1.0000 |
| No-op | not run before hardening | 0.0000 |
| Cheat 1 | 0.3347 | 0.0096 |
| Cheat 2 | 0.5030 | 0.0606 |
| Cheat 3 | 0.5357 | 0.0979 |
| Cheat 4 — complete Go port | 1.0000 | 1.0000 |

Reward JSONs are in `proof/`; full criterion details for the Day 5 reruns are in
`measure/attacker-reruns/`.

## Exam comparison

| Port | Wrong on old 2K exam | Wrong on new 100K exam | Old exam caught it? |
| --- | ---: | ---: | --- |
| Nitin oracle | 0 | 0 | No errors |
| Adarsh Sahani complete Go port | 0 | 0 | No errors |
| Ayush Ranjan Go port | 47 | 10,833 | Yes |

The new exam was frozen in `regex` mode, with 100,000 stable cases. Full comparison
reports are in `measure/`.

## What surprised me

Increasing the exam size exposed 10,833 errors in Ayush's port, although its older exam
had only 47. At the same time, a proper full Go port passed all 100,000 cases. A hardened
exam should make shortcuts fail while still giving correct implementations full credit.

## Day 6 retest status

The saved Harbor results in `proof/` are my reruns of Adarsh's published cheat scripts on
the hardened task. Cheats 1–3 meet the below-0.2 target. Cheat 4 remains at 1.0 because
it is correct. I have not edited Adarsh's `ATTACK.md`; the separate attacker-owned re-attack
entry and any new cheat must be appended by Adarsh.
