# DEFENCE.md - Ashish

Notes for the 5-minute talk, and the long form of the three points in
`HARDEN.md` under "What I learned".

> **Status: Day 6.** My own three proofs are run and `proof/` is written. The
> one thing still outstanding is Priyanshu re-running his cheats on my hardened
> task, which is his action, not mine. Every number below comes from a real
> `harbor run`, with the job folder named.

---

## 1. The strongest cheat against my task, before and after

**Cheat 1, "read the exam"** - `training-3/PriyanshuSingh/attack/cheat1/solve.sh`.
A Go program with no titlecase logic at all. It walked `/tests`, `/solution`,
`/logs`, `/workspace`, `/root`, `/tmp` and `/`, looked for an inputs file sitting
next to an answers file, built a lookup table and printed the stored answer.
Anything it could not find, it echoed back unchanged.

| | Score | Job folder |
|---|---:|---|
| Before | **1.0** | `jobs/pre-cheat1/scratch-c1__rWA43Tg` |
| After | **0.00** | `jobs/net-cheat1/netc1__JxLiDsz` |

Cheat 2 also scored 1.0, so "strongest" is a tie on score. Cheat 1 is the one
worth presenting, because it is the one where a 0.00 could have been a lie.

### Why the 0.00 is believable, which matters more than the 0.00

A fixed cheat can score 0 for the wrong reason: because I broke it, or because
the harness failed, not because the hole is closed. So I did not accept the
number on its own.

The verifier log for the hardened run says:

```
behaviour: matched 2175 of 100000 lines (rate 0.021750) -> score 0.000000
```

2,175 is **exactly** the number of lines in my exam where the input already
equals the correct answer - I counted it independently from `key/inputs.txt` and
`key/answers.txt`. That is precisely what cheat 1's "echo the line back"
fallback earns when its lookup table is empty. So the table contributed **zero**
answers: it is not that the cheat got worse, it is that it found nothing.

The same measurement on the old exam closes the argument: there, the
echo-unchanged baseline was **0 of 2,000**. So cheat 1's original 1.0 came
*entirely* from reading the answer file. Nothing else.

### What actually closed it - three changes, not one

1. `task.toml`: `[verifier] environment_mode = "separate"`. Grading moved into
   its own container, so `tests/` is never on disk while the agent is working.
   Only `artifacts = ["/workspace/repo"]` crosses over.
2. `tests/test.sh`: `chown -R 0:0` and `chmod -R go-rwx` on `/tests` before
   anything from the submission runs.
3. `tests/checks/behaviour.sh`: the compiled binary is installed to
   `/var/grader` and run under
   `setpriv --reuid=65534 --regid=65534 --clear-groups`. stdin and stdout are
   opened by root first, so the program never needs read access to the inputs,
   and `chmod -R go-rwx` on the submission means nothing the agent shipped is
   readable or executable by that user.

I verified the agent's side of this empirically rather than by reading my own
config: a probe "solution" that inventories the container reports `/tests`
does not exist, a filesystem-wide search for `answers.txt` / `inputs.txt` /
`hidden_*` finds nothing, and every interpreter is absent.

---

## 2. Before and after, the exam

Old exam: 2,000 inputs from 7 templates and one seed.
New exam: 100,000 inputs, mode `re` (**without** the `regex` package), 0 dropped
by the double freeze.

| Port | Wrong on new exam | Old exam caught it? | 2K random misses them all |
|---|---:|---|---|
| my oracle (after fixing it) | 0 | n/a | n/a |
| my oracle (as attacked) | 8,636 | **no** - 0 of 2,000 | 0% |
| MohammadAdnan | 99,485 | **no** - 0 of 2,000 | 0% |
| NehaGaur | 8,022 | **no** - 0 of 2,000 | 0% |
| OmarGhyas | 6,583 | **no** - 0 of 2,000 | 0% |
| PriyanshuSingh | 0 | n/a | n/a |
| Charitra | 0 | n/a | n/a |
| MadhurJain | 0 | n/a | n/a |

All seven `compare.py` outputs are in `measure/`; the method and the selection
reasoning are in `measure/survey.txt`.

**The line to say out loud:** every port I measured passes the old 2,000-line
exam with 0 wrong, including one that is wrong on 99,485 of 100,000 and my own
broken oracle. The old exam was not merely small, it was blind.

### The long version of "what was in it, not how big it was"

My old exam could not even tell the two modes of the original apart. Freezing
the same 100,000-line pool with the `regex` package changes **6,583** answers;
freezing the old 2,000 inputs both ways changes **0**. A port built for either
mode scored 1.0 on my old exam, which is why `instruction.md` now states the
mode, with that number in it.

Size still matters, but second. MohammadAdnan's fatal bug is triggered by
**exactly one** input out of 100,000 - the empty line - and a random 2,000-line
exam contains that input only **2.0%** of the time. Realigned past the single
line it swallows, it is wrong on only 149 of 99,999. One input decides whether
you see a catastrophic bug or none of it.

### Honest gap in the measurement

I was asked for one port with the most wrong and one with only a handful wrong.
The six surveyed ports came out 0, 0, 0, 6,583, 8,022 and 99,485 - **nothing
between 1 and 100**. The survey was capped at six, so such a port probably
exists elsewhere in the class; I did not find one and did not pretend to.
NehaGaur is the second row instead.

---

## 3. The surprise: the new exam broke my own oracle

8,636 wrong of 100,000. Four real bugs, none reachable from the old exam. I
changed no input and no answer.

### The long version of "writing the oracle is not understanding the original"

The bug I will actually be asked about is the third one.

`titlecase/__init__.py:29` defines `PUNCT`, and `_` is a member of it. My port
had a comment asserting the opposite - "`_` is a word character, not
punctuation" - and left it out of the class. That accidentally produces the
right answer in `CAPFIRST` (`:48`), because its `[PUNCT]*?` is **lazy**, so
`[\w]` gets first refusal and swallows the `_`. It produces the wrong answer in
`SMALL_FIRST` (`:33`) and `SMALL_LAST` (`:34`), whose `[PUNCT]*` is **greedy**.
So `_a` should become `_A` as a first word, and `vs._` should become `Vs._`.

**Commit `79fe2fd` in this repo is titled "fix capFirst for words starting with
`_`".** I had already met this bug, fixed the one symptom I could see, written
myself a comment justifying the wrong model, and left the identical mistake in
two other functions. The old exam contained no `_`-prefixed word anywhere, so it
agreed with me.

The other three, briefly:
- `UC_ELSEWHERE` (`:47`) is used as `.match()` at `:145`, which is **anchored**.
  I had implemented a search. So `X-RAY` looked like `iPhone`, the word was
  returned untouched, and the hyphen branch at `:160` never ran. 4,091 words.
- Go's `unicode.ToUpper`/`ToLower` are **simple** mappings; Python's
  `.upper()`/`.lower()` are **full** and may change length. `'ß'.upper()` is
  `SS`, `'ﬁ'.upper()` is `FI`, `'ŉ'.upper()` is `ʼN`, `'İ'.lower()` is
  `i` + U+0307. Go produces none of those. 4,740 words.
- My rewrite of `applyApos` dropped the optional `(?:['s]{2})?` tail of
  `APOS_SECOND`, so `o'reilly's` came out `O'reilly's`. The original code was
  also wrong under backtracking: `[\w]+` is greedy and gives characters back, so
  `o'reillys'` matches with `W="reilly"`, `T="s'"`.

### Why the fix is not tuned to the exam

The case table was **generated**, not hand-listed: a Go program printed
`ToUpper/ToLower/ToTitle` for all 1,112,064 code points, Python printed
`.upper()/.lower()/.capitalize()` for the same, and every disagreement became a
row. 157 rows, 44 of them above the BMP.

Generating it found two more problems the exam cannot see:

- My first generator emitted `\u10d50` for code points above U+FFFF. Go reads
  `\u` as exactly four hex digits, so that silently compiled as `U+10D5`
  followed by `'0'`. 44 rows of corrupt data that still built cleanly.
- Go 1.23 ships Unicode 15.0, CPython 3.14 ships Unicode 16.0. **5,004** code
  points are letters or numbers to Python and unassigned to Go, so
  `unicode.IsLetter` returns false and `\w`, `\b` and `CAPFIRST` all disagree.
  Embedded as 27 ranges, plus 5 for the Cased property. `\s` differs on exactly
  4 code points, U+001C-001F.

I also implemented `Final_Sigma` and simple-fold matching so `ſ` matches the `s`
in `as` and `vs`, as `re.IGNORECASE` does. None of that appears in my pool, so
it was verified against Python on a separate **1,586-line probe set** - 0
mismatches. `kit/gen_case_table.py` and `kit/make_probes.py` are pushed, and
re-running them reproduces the tables and every probe line byte for byte.

---

## 4. The long version of "absence, not detection"

Cheat 2 kept the original `titlecase/__init__.py` under a non-`.py` name,
embedded it with `go:embed`, and shelled out to the `python3` that `golang:1.23`
inherits from Debian. `tests/test.sh:21` only ever looked at file **names**.

The fix is not a better name check, a content heuristic or a shebang scan - all
of which an attacker gets to iterate against. `environment/Dockerfile` deletes
every scripting interpreter from the image and **fails the build** if
`command -v` can still find one. Because Harbor builds the separate verifier
container from a fresh copy of the same `[environment]`, one deletion covers
both containers.

| | Score | Job folder |
|---|---:|---|
| Before | **1.0** | `jobs/pre-cheat2/scratch-c2__5kEFFu8` |
| After | **0.00** | `jobs/net-cheat2/netc2__e2zpwhY` |

Verifier log: `behaviour: the program exited 1`, then `matched 0 of 100000`.
There is nothing to call.

This is also why `tests/` is pure shell instead of rewardkit: rewardkit has to
run **inside** the verifier, so Python would have to stay in the image, and
cheat 2 could then only be blocked by file permissions instead of absence.

The same reasoning drove the network change, and measuring it taught me
something I had wrong. `task.toml` now sets `network_mode = "no-network"` on
`[agent]` and `[verifier]`. On Harbor's Docker backend that is enforced by an
egress-control sidecar, **not** by `network_mode: none`, so `eth0` still exists
and DNS still resolves - `getent hosts pypi.org` returns exit 0. What stops is
data transfer: an HTTP GET to pypi.org returns **0 bytes**, `go mod download`
exits 1 with `EOF`, and every `apt-get update` fetch reports
`Connection failed` (`jobs/probe-net2/probe-net2__AtjA2r5`).

**If I am asked which single change matters most for cheat 2, the honest answer
is that it takes two.** I deleted Python with `rm -rf`, not `apt purge`, so dpkg
still lists 7 python3 packages as installed. With network,
`apt-get install --reinstall python3-minimal` would restore `/usr/bin/python3`
and cheat 2 would work again. Offline it fails -
`Reinstallation of python3-minimal is not possible, it cannot be downloaded` -
and the apt cache is empty, so the interpreter stays absent
(`jobs/probe-net3/probe-net3__WkfiPCX`). So "absence" is really "the files are
gone AND nothing can be downloaded to bring them back".

---

## Things I expect to be asked, and the honest answers

**"Isn't a 0.90 floor on partial credit just rigging it so cheat 3 fails?"**
Cheat 3 scores 19,529/100,000 = 19.5% on the hardened exam, down from
837/2,000 = 41.9% on the old one. 19.5% would already have been below the 0.2
bar under straight per-line credit. I added the floor anyway, because passing by
0.005 is not a defence. A near-correct port still earns credit: 95% of the lines
is worth 0.50.

**"You deleted the old exam files. Did you remove inputs your port failed?"**
No. The order of events is in the git history: the 100k exam went in first, my
port then failed 8,636 of it, and I fixed `solution/solve.sh`. The deleted files
are the old 2,000-line exam, superseded in full, and the patched port still
scores 0 wrong on them. `tests/gen.py` was deleted because it regenerates a
2,000-line exam over `tests/data/` and would destroy the new files.

**"Why is `nop` failing on `no_python` rather than on the build?"**
Because `nop` does nothing, so the vendored python-titlecase `.py` files are
still there, and that is gate 1. It reaches 0.0 either way, but the log says
`no_python: a .py file is still present`, and I would rather quote the real
reason than the one I expected.

**"What did you not fix?"**
Two things.

`go build ./...` still runs as root in the verifier, before privileges are
dropped. I am not aware of a way to execute attacker code during a build with
`GOTOOLCHAIN=local`, no network and no cgo toolchain tricks I could get to work,
but I did not prove it impossible and I am not going to claim I did.

`environment/Dockerfile` removes the interpreters with `rm -rf` rather than
`apt-get purge`, so dpkg's package state still disagrees with the filesystem.
Nothing can exploit it while the network is off, and I verified that, but the
tidy fix is a purge. I left it because purging could remove a package
`golang:1.23` depends on, and I was not willing to ship an unverified change to
the image after the proofs were already green.

---

## Day 6 proofs

| Run | Must be | Got | Job folder |
|---|---|---:|---|
| `harbor run -p task -a oracle` | 1.0 | **1.0** | `jobs/net-oracle/hard__PzoVC5a` |
| `harbor run -p task -a nop` | 0.0 | **0.0** | `jobs/net-nop/hard__AwqUnUT` |
| cheat 1 - read the exam | < 0.2 | **0.0000** | `jobs/net-cheat1/netc1__JxLiDsz` |
| cheat 2 - Python inside | < 0.2 | **0.0000** | `jobs/net-cheat2/netc2__e2zpwhY` |
| cheat 3 - half port | < 0.2 | **0.0000** | `jobs/net-cheat3/netc3__3e2KKt9` |

Reward files copied out to `proof/oracle-reward.json`, `proof/nop-reward.json`
and `proof/cheats-reward.txt`. The last of those also carries the verifier log
line behind each 0, because a 0 on its own does not tell you whether the hole is
closed or the cheat is broken.

An extra confirmation run against the byte-exact pushed task:
`jobs/final-oracle/final__aViDy8w` = 1.0.

---

## My own Day 6 re-attack, on Omar Ghyas (the other half of the pairing)

I also had to re-attack my Day 4 target. Recorded in full at the end of
`attack/ATTACK.md`; re-attacked commit `9e43b9c`.

| My cheat | Day 4 | Day 6 | Below 0.2? |
|---|---:|---:|---|
| 1 - lookup table | 0.3897 | **0.0130** | yes |
| 2 - half port | 0.7213 | **0.2936** | **no** |
| 3 - silent binary | 0.3333 | **0.0000** | yes |

Worth saying in the talk, because it is the same lesson from the other side: he
zeroed the `build`/`no_python` weights and stopped shipping the visible answer
key, which killed two of my three cheats outright. What he did not add was a
floor under partial credit - `tests/support.py:100` is still
`return matches / len(expected)` - so my half port still banks 0.2936. His
weirder 100,000-line pool cut it from 0.582 to 0.2936 and could not do better,
because the score *is* the match rate. That is exactly the step I did take on my
own task, and it is why cheat 3 scores 0.00 against me instead of 0.195.

His task also does not build as pushed: `docker-compose.yaml:5` still points at
`titlecase-go/environment/Dockerfile` after the Day 4 rename to `task/`, so
Harbor fails before grading and writes no reward file. I reconstructed only the
folder layout his own compose file expects, edited nothing of his, and his
oracle then scores 1.0.

---

## Still outstanding

- [ ] Priyanshu re-runs his three cheats on my hardened task and may try one new
      cheat, then appends the results to his own `ATTACK.md`. He needs telling
      that the hardened task is ready.
- [ ] Give the talk.
