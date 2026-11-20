# Attack on Ashish's titlecase-go task

Target: `Ashishreliable/titlecase-go` at commit `d0f6618c3e98c53d2ee133301080289f7a24aa92`
(see `TARGET.txt`). Harbor 0.25.0, Docker 29.9.2, Windows 11. All runs on 2026-11-18.

Every cheat was run with `harbor run -p attack/scratch/cheatN -a oracle -o jobs`,
where `attack/scratch/cheatN` is an untouched copy of the target with only
`solution/solve.sh` replaced. `tests/`, `task.toml` and `environment/` were not edited.

Baseline: the target's own oracle scores **1.0** (`jobs/target-oracle/target__d3Z3hGS`).

## What the exam is (read before attacking)

| Question | Answer | Where |
|---|---|---|
| What the agent sees in the container | Only `/workspace/repo/Dockerfile`. The image copies the `environment/` folder, which holds nothing but the Dockerfile, so the python-titlecase source the instruction promises is **not there**. | `environment/Dockerfile:3-4`, `instruction.md:5` |
| Is Python in the image | Yes, `python3` 3.11.2 (comes with `golang:1.23`) | `environment/Dockerfile:1` |
| What `test.sh` checks | Gate 1: any `.py` file under the repo → 0. Gate 2: `go build ./...` fails → 0. Then reward = share of hidden lines that match exactly. | `tests/test.sh:21`, `:26`, `:51-78` |
| Which inputs | 2,000 hidden lines in `/tests/data/hidden_inputs.txt` + `hidden_expected.txt`, made by `gen.py` from the same templates as the 2,000 visible lines | `tests/test.sh:12-13`, `tests/gen.py:154-226` |
| Is `tests/` visible | Not during the agent's turn, but **yes while the graded binary runs**: it runs as root in the same container, with `/tests` on disk and readable | `tests/test.sh:43` |

Three weakest points:
1. The program is run as root next to the answer files (`tests/test.sh:12-13`, `:43`).
2. "No Python" only looks at file names, and the image has python3 (`tests/test.sh:21`, `environment/Dockerfile:1`).
3. Partial credit per line on a small, template-made exam: easy rules alone get a big share (`tests/test.sh:51-78`, `tests/gen.py:154-226`).

Side note: the task's own cheat (`cheat/solve.sh:23`) opens `tests/data/expected.txt` by a
relative path that does not exist at run time, so it scores 0. That hides the real hole
found by Cheat 1.

---

## Cheat 1 — Read the exam

```
What it does:   A Go program with no titlecase logic. At run time it walks /tests, /solution,
                /logs, /workspace, /root, /tmp and / for *_expected.txt / answers.txt files,
                pairs them with the inputs file next to them, and prints the stored answer.
Score:          reward 1.0   (all-or-nothing gates passed; 2000 / 2000 hidden lines "right")
Job folder:     jobs/ashish-cheat1/cheat1__iwtAAQ2
Why it worked:  tests/test.sh:12-13 keeps the answers in $SCRIPT_DIR/data (= /tests/data), and
                tests/test.sh:43 runs "$BIN" as root in the same container, so the program
                can simply open /tests/data/hidden_expected.txt.
How to fix:     Run the program as an unprivileged user (e.g. nobody) after `chmod -R go-rwx /tests`,
                or grade in a separate verifier container that holds the answers out of reach.
```

Honest note: my first version of this cheat scored 0.005 because of a bug in the cheat
(it marked `/tests/data` as done after finding `expected.txt` and never loaded
`hidden_expected.txt`). That was my bug, not a strength of the exam. The fixed version is
the one in `cheat1/solve.sh`, and the job folder above is its run.

## Cheat 2 — Python inside

```
What it does:   Stores the original python-titlecase __init__.py, unchanged, as tc_source.txt
                (not .py), embeds it in the Go binary with go:embed, and at run time feeds it
                to the python3 already in the image. No titlecase logic in Go at all.
Score:          reward 1.0   (no .py file, build passes, 2000 / 2000 hidden lines right)
Job folder:     jobs/ashish-cheat2/cheat2__2yK45uv
Why it worked:  tests/test.sh:21 only checks for files named *.py, and
                environment/Dockerfile:1 (golang:1.23) ships /usr/bin/python3, which the
                graded binary can call at tests/test.sh:43.
How to fix:     Remove Python from the image the program runs in (rm /usr/bin/python3*), or run the
                program in a verifier image with no Python, as a user that cannot reach any.
```

## Cheat 3 — Half port

```
What it does:   ~40 lines of Go with only the easy rules: lower-case an all-caps line, capitalise
                each word, keep a fixed list of small words lower case unless first/last, leave
                words with an inner capital alone. No URLs, e-mails, hyphens, Mc, apostrophes.
Score:          reward 0.4185   (837 / 2000 hidden lines right)
Job folder:     jobs/ashish-cheat3/cheat3__7ECvvpX
Why it worked:  tests/test.sh:51-78 gives one point per matching line, and the hidden lines come
                from the same 7 simple templates as the visible ones (tests/gen.py:154-226), so
                plain "capitalise every word" lines are a large share of the exam.
How to fix:     Grade on a much bigger and weirder pool (URLs, Mc-, d'Arcy, tabs, NBSP, ı, v1.2 …),
                and make partial credit smaller, e.g. no reward below a high match rate.
```

---

**Highest score any cheat got: 1.0** (Cheat 1 and Cheat 2).
