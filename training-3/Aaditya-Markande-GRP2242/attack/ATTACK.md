# ATTACK.md: attack on Akshat Tomar's titlecase-go task

Attacker: Aaditya Markande
Target commit: dc7de0dcb1ca554c3e58756107dfe95a55a3b04d (see TARGET.txt)

## How the target scores
`tests/checks.py` ends with `rk.build(weight=1)` (line 120), `rk.no_python(weight=1)` (line 121) and `rk.behaviour(weight=4)` (line 122). The reward is the weighted mean, so the total is divided by 6.

## Run note
The grader downloads packages with `uvx` at grading time (`tests/test.sh`). It timed out twice in my Codespace (RewardFileNotFoundError; folders `jobs/failed-cheat1-network-timeout` and `jobs/failed-cheat1-try2`). I re-ran with the Harbor options `--ve UV_HTTP_TIMEOUT=300 --ve UV_CONCURRENT_DOWNLOADS=2`. I did not touch `tests/`, `task.toml` or `environment/`.

## Cheat 1: Delete trick + empty program
What it does:   Deletes every `*.py` in /workspace/repo, writes a go.mod and a main.go that copies stdin to stdout. It also searches the disk for hidden_inputs.txt, hidden_expected.txt and expected.txt (found nothing).
Score:          reward 0.3843 (build 1.0, no_python 1.0, behaviour 0.0765)
Job folder:     jobs/attack-cheat1/scratch1__PbSKQ5U
Why it worked:  `tests/checks.py:120-121` give build and no_python weight 1 each, so 2 of 6 points (0.333) come with no real work. `no_python` (line 90) passes whenever the build passes and no `*.py` file exists. The echo program also matches 153 of 2000 lines (blank and whitespace-only lines) through `_line_fraction` (line 74).
How to fix:     Pay build and no_python only when behaviour is high, for example final reward = 0 if behaviour < 0.99.

## Cheat 2: Half port (easy rules only)
What it does:   Go program that capitalises each word and keeps small words lowercase unless first or last. It skips Mc names, apostrophes, hyphens, slashes, URLs, mixed case and uppercase lines.
Score:          reward 0.5577 (build 1.0, no_python 1.0, behaviour 0.3365)
Job folder:     jobs/attack-cheat2/scratch2__NAKz5Sg
Why it worked:  `_line_fraction` (`tests/checks.py:74`) gives credit for every matching line, so a wrong port matches 673 of 2000 lines and earns 4 x 0.3365 behaviour points on top of the 2 free points.
How to fix:     Make behaviour all-or-nothing, or give no credit below about 99% of lines correct.

## Cheat 3: Python inside (the strongest)
What it does:   Copies the original Python source to pysrc/titlecase_init.txt, deletes every `*.py`, and builds a tiny Go wrapper. The wrapper embeds the text with go:embed, writes it back out as Python into a temp dir at run time, and runs `python3` on every input line.
Score:          reward 1.0 (build 1.0, no_python 1.0, behaviour 1.0)
Job folder:     jobs/attack-cheat3/scratch3__yMQ576W
Why it worked:  `tests/checks.py:40` only checks file names with `workspace.rglob("*.py")`, so Python under another name is invisible. The image has Python 3.11.2 (both `environment/Dockerfile` and `tests/Dockerfile` start FROM golang:1.23), and the original source sits at /workspace/repo/titlecase/__init__.py because `environment/Dockerfile` copies python-titlecase/ there. The wrapper's output equals the original's, so behaviour is 1.0.
How to fix:     Remove python3 from both images (uv fetches its own Python for the grader), scan file contents and imports (for example reject os/exec and go:embed), and run the binary in a container with no python3.

## Other findings (no score)
- Strong point: the hidden answers are not reachable by the agent. Cheat 1's disk search found no exam file, and `task.toml` sets `environment_mode = "separate"`.
- Fragile grader: `tests/test.sh` runs `uvx --from harbor-rewardkit==0.2.4` and needs the internet every time. Fix: install rewardkit once in `tests/Dockerfile`.
- Small, plain exam: `tests/gen.py:13` sets COUNT = 2000, and the NORMAL list (line 40) holds plain lowercase words. There are no digits, no odd Unicode and no unusual punctuation.
- `task.toml` sets `network_mode = "public"` for the agent and the verifier, so an agent could download a ready-made port.

Highest score any cheat got: 1.0 (cheat 3)

## Day 6 re-attack
(to be added after Akshat hardens his task)
