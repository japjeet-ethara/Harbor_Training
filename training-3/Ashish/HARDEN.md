# HARDEN.md - Ashish, Day 5

Attacker: **Priyanshu Singh**, report at `training-3/PriyanshuSingh/attack/ATTACK.md`.
Target he attacked: `Ashishreliable/titlecase-go` at commit `d0f6618c3e98c53d2ee133301080289f7a24aa92`.

That commit is byte-identical to my Day 4 copy:
`git diff --no-index --stat Ashishreliable/titlecase-go training-3/Ashish/task` printed
nothing, so all three of his cheats apply to `training-3/Ashish/task` unchanged.

Harbor 0.25.0, Docker 29.9.2 (Docker Desktop), WSL2 Ubuntu. All numbers below come
from real `harbor run` jobs; the job folder is next to each one.

---

## Step 5.1 - his cheats re-run on my task, before any change

I re-ran all three myself from his `attack/cheatN/solve.sh` blobs, each in a fresh
copy of my task with only `solution/solve.sh` replaced.

| Cheat | His score | My re-run | Job folder |
|---|---:|---:|---|
| 1 - read the exam | 1.0 | **1.0** | `jobs/pre-cheat1/scratch-c1__rWA43Tg` |
| 2 - Python inside | 1.0 | **1.0** | `jobs/pre-cheat2/scratch-c2__5kEFFu8` |
| 3 - half port | 0.4185 | **0.4185** | `jobs/pre-cheat3/scratch-c3__3rFvVPh` |

His numbers reproduce exactly. Baseline oracle 1.0 (`jobs/base-oracle/base__WQqj2B6`).

**One thing he could not have seen.** My task was unrunnable from a Windows checkout.
This repo has `core.autocrlf=true` and my folder had no `.gitattributes`, so
`solution/solve.sh`, `tests/test.sh` and all four data files came out of `git checkout`
with CRLF line endings. The first thing Harbor said was
`/solution/solve.sh: cannot execute: required file not found` - a CRLF shebang.
Fixed with `training-3/Ashish/.gitattributes` (`* text=auto eol=lf`). This is not one
of his cheats, it is a bug the exercise flushed out, and it would have scored every
answer wrong anyway because the Go port prints LF and the answers ended in `\r`.

---

## Holes closed

### Cheat 1 - read the exam: was 1.0, now 0.00 (`jobs/net-cheat1/netc1__JxLiDsz`)

His Go program had no titlecase logic. It walked `/tests`, `/solution`, `/logs`,
`/workspace`, `/root`, `/tmp` and `/`, found an inputs file next to an answers file,
and printed the stored answer. It worked because `tests/test.sh:12-13` kept the answers
in `$SCRIPT_DIR/data` and `tests/test.sh:43` ran `"$BIN"` **as root in the same
container** as those files.

Three changes, not one:

1. `task.toml` now sets `[verifier] environment_mode = "separate"`, so grading happens
   in its own container and `tests/` is never on disk while the agent works.
   `artifacts = ["/workspace/repo"]` is all that crosses over.
2. `tests/test.sh:41-42` does `chown -R 0:0` and `chmod -R go-rwx` on `/tests` before
   anything from the submission runs, so `/tests` is root-only.
3. `tests/checks/behaviour.sh:50-70` installs the compiled binary to `/var/grader` and
   runs it under `setpriv --reuid=65534 --regid=65534 --clear-groups`. Standard input
   and output are opened by root first, so the program never needs read access to the
   inputs. `chmod -R go-rwx "$REPO"` also makes everything the agent shipped unreadable
   and unexecutable by that user.

I also checked the agent's side of this empirically instead of reading my own config. A
probe "solution" that inventories the container reports: `/tests` does not exist, a
filesystem-wide search for `answers.txt`, `inputs.txt` and `hidden_*` finds nothing, and
`python`, `python3`, `perl`, `ruby`, `node` and `php` are all absent
(`jobs/probe-agent/probe-agent__FrmPprz`).

**How I know the fix is real, not luck.** The verifier log says
`behaviour: matched 2175 of 100000 lines`. 2,175 is exactly the number of lines in my
exam where the input already equals the answer, which is what his "echo the line back"
fallback earns. Its lookup table contributed **zero** answers. On the old exam that same
baseline was 0 of 2,000, so his 1.0 there came entirely from reading the answer file.

### Cheat 2 - Python inside: was 1.0, now 0.00 (`jobs/net-cheat2/netc2__e2zpwhY`)

He stored the original `titlecase/__init__.py` unchanged as `tc_source.txt`, embedded it
with `go:embed`, and shelled out to the `python3` that `golang:1.23` inherits from
Debian. `tests/test.sh:21` only ever looked at file **names**.

`environment/Dockerfile:18-30` now deletes every scripting interpreter from the image -
`python3*`, `python`, `/usr/lib/python3*`, `perl`, `ruby`, `node`, `php` - and the build
**fails** if `command -v` can still find any of them. Because Harbor builds the separate
verifier container from a fresh copy of this same `[environment]`, one deletion covers
both containers.

Verifier log: `behaviour: the program exited 1`, `matched 0 of 100000`. There is no
interpreter left to call. I deliberately did not try to detect this by name, filename or
heuristic: the interpreter is simply absent.

One route was still open after that: the agent had network, so it could have fetched an
interpreter and shipped it inside the artifact. `task.toml` now sets
`network_mode = "no-network"` on both `[agent]` and `[verifier]`.

I measured what that actually does rather than trusting the name. On Harbor's Docker
backend `no-network` is enforced by an egress-control sidecar, **not** by
`network_mode: none` on the container, so `eth0` still exists and DNS still resolves.
What stops is data transfer:

| Probe inside the agent container | Result |
|---|---|
| `getent hosts pypi.org` | exit 0 - still resolves |
| HTTP GET to pypi.org | **0 bytes received** |
| `go mod download github.com/google/uuid` | **exit 1**, `EOF` |
| `apt-get update` | every fetch `Connection failed` |

Probe job folder: `jobs/probe-net2/probe-net2__AtjA2r5`.

**And this is load-bearing, not a nicety - I had it filed wrongly at first.** I removed
Python with `rm -rf`, not `apt purge`, so dpkg still lists 7 python3 packages as
installed. With network, `apt-get install --reinstall python3-minimal` would put
`/usr/bin/python3` back and cheat 2 would work again. Offline it fails -
`Reinstallation of python3-minimal is not possible, it cannot be downloaded` - and
`/var/cache/apt/archives` is empty, so the interpreter stays absent
(`jobs/probe-net3/probe-net3__WkfiPCX`). So "the interpreter is absent" rests on two
layers: the files are gone, and nothing can be downloaded to bring them back. A cleaner
version of this task would `apt-get purge` the packages so dpkg state matches reality;
I chose not to, because purging could pull out a package `golang:1.23` depends on and I
did not want an unverified change in the image this late.

This is also why `tests/` is pure shell rather than rewardkit. Rewardkit has to run
inside the verifier, which would mean Python must stay in the image and cheat 2 could
only be blocked by file permissions instead of absence.

### Cheat 3 - half port: was 0.4185, now 0.00 (`jobs/net-cheat3/netc3__3e2KKt9`)

About 40 lines of Go with only the easy rules - no URLs, e-mails, hyphens, slashes,
Mc/Mac, apostrophes, initials or sub-phrases. `tests/test.sh:51-78` paid straight
per-line credit over 2,000 template-generated lines, so it collected 837/2000 = 0.4185.

Two changes:

1. The exam is now 100,000 weird inputs instead of 2,000 template ones. The same cheat
   drops from **837/2000 = 41.9%** to **19,529/100,000 = 19.5%** on correctness alone.
2. `tests/checks/behaviour.sh` puts a floor under partial credit: below a 0.90 line
   match rate the score is 0.0, from 0.90 to 1.00 it ramps linearly, and only a
   byte-identical whole stream is 1.0. A near-correct port still gets credit - 95% of
   the lines is worth 0.50 - but 19.5% is worth nothing.

Note that 19.5% would already have been just under the 0.2 bar without the floor. I
added the floor anyway, because 0.195 passing by 0.005 is not a defence.

### Not one of his cheats, but the same class of hole

`build` and `no_python` used to be the only things standing between a submission and a
score, and in his read of the task they were worth points elsewhere. In my task they are
now explicitly **gates that pay nothing**: `tests/test.sh` runs
`checks/no_python.sh` and `checks/build.sh`, and a failure writes 0.0 and stops. A
submission that passes both and prints nothing scores 0.0, which is what `nop` does
(`jobs/net-nop/hard__AwqUnUT`, reward 0.0, log: `no_python: a .py file is still present`).

`environment/Dockerfile` also fixes something he caught but could not exploit:
`instruction.md:5` promised python-titlecase in `/workspace/repo`, but the old Dockerfile
said "the build context is ../python-titlecase" and ran `COPY . /workspace/repo`, so the
agent got a directory containing nothing but the Dockerfile. The pristine 2.4.1 snapshot
is now vendored in `environment/python-titlecase/` and really is copied in.

---

## The new exam

```
kit/make_pool.py 100000 1 pool.txt          -> 100,000 unique inputs, 3.4 MB
kit/answers.py <python-titlecase> pool.txt key
```

`kit/report.txt`:

```
pool inputs        100000
kept (stable)      100000
dropped (unstable) 0
regex module used  False
```

`answers.py` runs the original twice under different `PYTHONHASHSEED` values and keeps
only inputs that answer identically both times. **0 dropped.**

**Mode: WITHOUT the `regex` package (`import re as regex`, `REGEX_AVAILABLE` is False).**
Stated in `instruction.md` under "Which original", with the reason and an example.

I added seven word families to the trainer's `make_pool.py` that my old exam never
produced: inner `@` e-mail addresses, digits and ordinals, all-caps hyphenated acronyms
(`X-RAY`, `T-SHIRT`), characters whose upper or title case grows (`ß`, `ﬁ`, `ﬂ`, `ŉ`,
`İ`, `ǅ`), decomposed NFD accents, `_`-words (`_dream`, `__init__`), and `//`. Plus
line-level shapes: leading and trailing whitespace, and the empty line.

**Mode sensitivity, measured (information only, the exam is `re` only).** Freezing the
same pool with the `regex` package gives **6,583 different answers out of 100,000**.
My old 2,000-line exam: **0 of 2,000**. The old exam could not tell the two modes apart
at all, which means it would have scored a port built for either mode as perfect.

---

## My own oracle failed the new exam. 8,636 of 100,000.

This is the most useful thing that happened all day. The exam was not changed; the port
was. Three real bugs, all invisible to the old exam:

**1. `UC_ELSEWHERE` used as a search instead of an anchored match - 4,091 words.**
`titlecase/__init__.py:47` is `[PUNCT]*?[a-zA-Z]+[A-Z]+?` and `:145` calls `.match()`,
which is anchored. My `hasUCElsewhere` scanned the whole word for "an uppercase letter
after a letter", so `X-RAY` looked like `iPhone`, the word was returned untouched and the
hyphen branch at `:160` never ran. `X-RAY` stayed `X-RAY` instead of becoming `X-Ray`
(1,230 times), `T-SHIRT` 1,038, `E-MAIL` 1,015.

**2. Go's simple case mapping is not Python's full case mapping - 4,740 words.**
`:183` is `CAPFIRST.sub(lambda m: m.group(0).upper(), word)`. Python's `.upper()` and
`.lower()` are *full* mappings and may change length; Go's `unicode.ToUpper` and
`strings.ToUpper` are one-rune-in, one-rune-out and silently do nothing:

| | Python | Go |
|---|---|---|
| `'ß'.upper()` | `SS` | `ß` |
| `'ﬁ'.upper()` | `FI` | `ﬁ` |
| `'ŉ'.upper()` | `ʼN` | `ŉ` |
| `'İ'.lower()` | `i` + U+0307 | `i` |

So `ﬁle`→`FIle`, `ßeta`→`SSeta`, and `İSTANBUL`→`İstanbul` where my port dropped the
combining dot and printed `Istanbul`. It also corrupted the all-caps test at `:106`.

**3. `_` wrongly left out of the PUNCT class - 55 words.**
`:29` PUNCT contains `_`. My port had a comment claiming it did not, and omitted it. That
accidentally works for `CAPFIRST` (`:48`), whose `[PUNCT]*?` is lazy so `[\w]` grabs `_`
first, but it breaks `SMALL_FIRST` (`:33`) and `SMALL_LAST` (`:34`), whose `[PUNCT]*` is
greedy. `_a` should be `_A` as a first word, `vs._` should be `Vs._`.

This is the one that stings: commit `79fe2fd` is titled "fix capFirst for words starting
with `_`". I patched the one symptom I could see and left the identical mistake in two
other functions, because the old exam contained no `_`-prefixed word anywhere.

A fourth bug surfaced while fixing those: my rewrite of `applyApos` dropped the optional
`(?:['s]{2})?` tail of `APOS_SECOND` (`:48`), so `o'reilly's` came out `O'reilly's`
(1,928 lines). The original code handled the common case but was also wrong under
backtracking - `[\w]+` is greedy and gives characters back, so `o'reillys'` matches with
`W="reilly"`, `T="s'"`. It is now modelled as the explicit split it is.

### How the fix was built, and why it is not tuned to the exam

The case table was **generated by diffing the two implementations**, not by listing the
characters the exam happened to contain: a Go program printed
`unicode.ToUpper/ToLower/ToTitle` for all 1,112,064 code points, Python printed
`.upper()/.lower()/.capitalize()` for the same, and every disagreement became a table
row. That is **157 rows**, of which 44 are above the BMP.

Generating it caught two further problems the exam cannot see:

- My first generator emitted `\u10d50` for code points above U+FFFF. Go reads `\u` as
  exactly four hex digits, so that silently compiled as `U+10D5` followed by `'0'` -
  44 rows of corrupt data that still built fine. Now `\U%08x`.
- Go 1.23 ships Unicode 15.0 and CPython 3.14 ships Unicode 16.0. **5,004 code points**
  are letters or numbers to Python and unassigned to Go, so `unicode.IsLetter` returns
  false and `\w`, `\b` and `CAPFIRST` all disagree. Embedded as 27 ranges
  (`unicode16Word`), plus 5 ranges for the Cased property. `\s` differs on exactly 4
  code points, U+001C-001F, which Python counts as whitespace and Go does not.

I also implemented the `Final_Sigma` rule (a capital sigma lowercases to `ς` at the end
of a word) and simple-fold matching so `ſ` matches the `s` in `as` and `vs`, the way
`re.IGNORECASE` does.

None of those last items appear in my pool. They were verified against Python on a
separate **1,586-line probe set** - every one of the 157 table code points in ten word
contexts, sigma in eleven contexts, `ſ` against the small-word list, and the four control
characters - with **0 mismatches**. The probe inputs are not part of the exam, and must
not be: their job is to stop me tuning the port to the exam.

Both generators are pushed, so none of this has to be taken on trust:
`kit/gen_case_table.py` and `kit/make_probes.py`. Re-running them reproduces the
157 case-table rows, the 27 + 5 ranges and all 1,586 probe lines **byte for byte**.

**After the fix: 0 wrong of 100,000**, and still 0 wrong on the old 2,000 hidden lines.

---

## Exam: before and after

Old exam: 2,000 inputs, 7 templates, one seed. New exam: 100,000 inputs, mode `re`.

| Port | Wrong on new exam | Old exam caught it? | Chance 2K random misses them all |
|---|---:|---|---|
| my oracle (after fixing it) | 0 | n/a | n/a |
| my oracle (as attacked) | 8,636 | **no** - 0 of 2,000 | 0% |
| MohammadAdnan | 99,485 | **no** - 0 of 2,000 | 0% |
| NehaGaur | 8,022 | **no** - 0 of 2,000 | 0% |
| OmarGhyas | 6,583 | **no** - 0 of 2,000 | 0% |
| PriyanshuSingh | 0 | n/a | n/a |
| Charitra | 0 | n/a | n/a |
| MadhurJain | 0 | n/a | n/a |

All seven `compare.py` outputs are in `measure/`, with the method and the selection
reasoning in `measure/survey.txt`.

**Every port I measured passes the old 2,000-line exam with 0 wrong** - including the one
that is wrong on 99,485 of 100,000 and my own broken oracle. The old exam was not merely
small, it was blind.

The two ports asked for were "the most wrong, not a crash" and "only a handful wrong":

- **MohammadAdnan, 99,485 of 100,000.** It never crashes and exits 0. It swallows the
  pool's single empty input line, so every later line shifts by one. Realigned past that
  one line it is wrong on only **149** - one line-contract bug amplified, not 99,485
  separate mistakes. A random 2,000-line exam contains that empty input only **2.0%** of
  the time.
- **A handful wrong: no port in my survey qualifies, and I am not going to invent one.**
  The six results were 0, 0, 0, 6,583, 8,022 and 99,485; nothing lands between 1 and 100.
  The survey was capped at six ports, so such a port may exist elsewhere in the class.
  NehaGaur is the second row instead.

**OmarGhyas is the clearest result of the whole measurement, and it is not a bug.** His
6,583 wrong lines are *exactly* the set of lines on which the two modes disagree, and he
matches the WITH-regex answers on **all 100,000**. His port is correct - for the other
original. That is the entire argument for stating the mode in `instruction.md`, measured
rather than asserted. NehaGaur's 8,022 are mostly the same thing seen through `CAPFIRST`
(`_dream`→`_Dream` 1,416, `__init__`→`__Init__` 1,454, `v1.2`→`V1.2` 1,528), plus 972
lines of the very full-case-mapping bug I had just fixed in my own port.

---

## Proofs on the hardened task

| Run | Required | Got | Job folder |
|---|---|---:|---|
| `harbor run -p task -a oracle` | 1.0 | **1.0** | `jobs/net-oracle/hard__PzoVC5a` |
| `harbor run -p task -a nop` | 0.0 | **0.0** | `jobs/net-nop/hard__AwqUnUT` |
| cheat 1 | < 0.2 | **0.0** | `jobs/net-cheat1/netc1__JxLiDsz` |
| cheat 2 | < 0.2 | **0.0** | `jobs/net-cheat2/netc2__e2zpwhY` |
| cheat 3 | < 0.2 | **0.0** | `jobs/net-cheat3/netc3__3e2KKt9` |

Every job folder above is a run against the `task.toml` in this commit. The same five
runs were made before `network_mode` was added and gave identical rewards
(`jobs/hard-oracle`, `jobs/hard-nop`, `jobs/hard-cheat1..3`); the network setting changed
no score, which is the expected result since it closes a route nothing was using yet.

---

## What I learned (3 lines)

1. My exam was weak because of *what* was in it, not because it was small: all seven ports I measured score 0 wrong on the old 2,000 lines (`measure/survey.txt`).
2. Writing the oracle is not the same as understanding the original: the new exam found four real bugs in my own port, 8,636 wrong of 100,000 (`measure/my-oracle.txt`).
3. The defence that holds is absence, not detection: cheat 2 died because no interpreter exists in the image at all (`jobs/net-cheat2/netc2__e2zpwhY`).

The long versions of these three, with the evidence behind each, are in `DEFENCE.md`.
