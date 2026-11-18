# my-org/figlet-go

Harbor practice task 2: port [pyfiglet](https://github.com/pwaller/pyfiglet)
(commit `255827e`, MIT) to Go, with output identical to the Python byte for byte,
for the options `-f -w -j -D -r -F -s -n`.

## Results (real Harbor runs, Docker, 18 Nov 2026)

| Run | build | no_python | behaviour | reward | secret |
|---|---|---|---|---|---|
| oracle (`solution/`) | 1 | 1 | 1.0 (2000/2000) | **1.0** | drawn ("well smushed, friend") |
| nop | 0 | 0 | 0 | **0.0** | no |
| cheat (`cheat/`) | 1 | 0 | 0 (0/2000) | **0.1667** | no |

Page secret (Step 8), built with the oracle's code inside the room: **go touch grass**.

## Layout

| Path | Seen by agent? | What it is |
|---|---|---|
| `instruction.md` | yes | The question paper |
| `environment/Dockerfile` | yes (it is the room) | Two stages: `alpine/git` fetches pyfiglet and does the font setup; `golang:1.23-alpine` + bash, user `player`, **no Python**. Both images are pinned by digest |
| `solution/` | no | `figlet.go` (full Go port, fonts embedded with `go:embed`) + `solve.sh` |
| `tests/` | no (copied in after the agent) | `grade.go` (Go grader), `test.sh`, `secret.b64`, `data/visible.jsonl`, `data/hidden.jsonl`, `gen.py` |
| `cheat/` | no | Cheat: looks up the visible answers, deletes `.py`. Must get < 0.2 |
| `tools/` | no | `compare.py` (first 5 wrong cases), `run-cheat.ps1` (one-command cheat check) |
| `NOTES.md` | no | Step 1 notes: SHA, licence, font setup, smushing rules, options |

## The six room rules (checked)

```
docker build -t figlet-room environment/
docker run --rm figlet-room sh -c 'whoami; pwd; ls pyfiglet/fonts | wc -l; command -v python3 || echo NO_PYTHON; command -v bash; touch x && echo CAN_WRITE'
```
→ `player`, `/workspace/repo`, `72`, `NO_PYTHON`, `/bin/bash`, `CAN_WRITE`.

## Scoring (`tests/grade.go`)

`reward = (build + no_python + 4 × behaviour) / 6`

- **build**: `go build -o /tmp/figlet .` works and `go.mod` has no `require` lines.
- **no_python**: the build passed, **and** there are no `.py` files, **and** at least one hidden case is right.
- **behaviour**: share of the 2000 hidden cases whose stdout matches exactly. Each case runs from a temporary directory with a 5 s timeout.

Expected by hand: nothing done = 0, build only = 1/6 ≈ 0.17, perfect = 1.0.

## How the answers were made (`tests/gen.py`, seed 7)

Every `out` is the stdout of the original `python -m pyfiglet` (run twice:
byte-identical). Visible and hidden argument lists never overlap. Cases were
**left out** when pyfiglet crashed (`CharNotPrinted` at narrow widths), hung
(some narrow widths loop forever), or printed only whitespace. Otherwise a
program that prints nothing would get those cases right for free, and the cheat
would earn `no_python` (about 0.43 instead of < 0.2).

## Extra checks on the Go port

- Font parsing compared with Python on **all 67** standard fonts (every glyph, width,
  hardblank, smush mode): 0 differences.
- Fuzzed against pyfiglet on 1169 random cases over all 67 fonts and widths 5–200,
  including 76 crash cases: 1169/1169 identical.

## Hand-in lines

1. *Rule that is hardest to get right:* right-to-left smushing. The rules see
   (new letter, buffer) instead of (buffer, new letter), and universal overlapping
   then keeps the *left* character. Close behind is pyfiglet's own big-X mapping
   (`\`+`/` → `Y`), which differs from C figlet.
2. *Docker traps hit:* Alpine has no `bash` (Harbor needs it), and narrow widths make
   pyfiglet crash or loop forever. Those cases had to be dropped from the answers,
   or the cheat would have scored about 0.43.

## Commands (PowerShell, from this folder)

```
harbor run -p . -a oracle -o ../jobs --job-name my-oracle
harbor run -p . -a nop -o ../jobs --job-name my-nop
powershell -ExecutionPolicy Bypass -File tools\run-cheat.ps1 -JobName my-cheat
harbor view ../jobs
```
