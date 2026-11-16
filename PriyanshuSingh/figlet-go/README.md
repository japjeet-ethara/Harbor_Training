# priyanshu/figlet-go

A Harbor practice task focused on porting [pyfiglet](https://github.com/pwaller/pyfiglet) to Go. The goal was to recreate the original Python implementation (MIT license, commit `255827e`) so that every supported command produces exactly the same large-text output, byte for byte, without leaving any Python files behind.

This task was based on Practice Task 2, *The Machine That Shouts in Giant Letters*.

## Results

The project was tested locally using Harbor 0.25.0 and Docker. Terminal captures of each run are in [`screenshots/`](screenshots/) (`oracle_reward.png`, `nop_reward.png`, `cheat_reward.png`).

| Run | Build (w1) | No Python (w1) | Behaviour (w4) | Reward | Target | Secret |
|---|---:|---:|---:|---:|---:|---|
| oracle | 1.0 | 1.0 | 1.0 | **1.0** | 1.0 | Drawn ("well smushed, friend") |
| nop | 0.0 | 0.0 | 0.0 | **0.0** | 0.0 | No |
| cheat | 1.0 | 0.0 | 0.0 | **0.1667** | Below 0.2 | No |

Running `harbor lint` produces only one warning: `shared-verifier`. This is expected for this practice task.

### Additional testing

A few extra checks were performed to make sure the implementation was reliable and that the grader could catch common mistakes.

- Running `gen.py` twice produces exactly the same files each time. Both runs generate 2,000 visible and 2,000 hidden cases. Each set contains roughly 800 right-to-left cases and 300 narrow-width right-to-left cases (widths 10 and 20).
- A second implementation that reads `/tests/data/hidden.jsonl` during grading, with help from a background process left running by the agent, also scores only 0.1667.
- A mutation test was performed by deliberately introducing bugs into the oracle implementation. The hidden tests detected every planted bug that can change the output.

The mutation results, showing the number of failed cases out of 2,000, are:

| Introduced bug | Failed cases |
|---|---:|
| Use `>` instead of `>=` when wrapping | 265 |
| Reset `prevCharWidth` to 0 after wrapping | 1197 |
| Right justification without subtracting `1` | 710 |
| Skip the right-to-left swap in `smushAmount` | 787 |
| Turn off the opposite-pair rule (`[]`, `{}`, `()` → `\|`) | 9 |
| Swap the `()` and `<>` classes in the hierarchy rule | 2 |
| Turn off the underscore rule | 307 |
| Turn off the equal-character rule | 702 |
| In universal smushing, let a hardblank win over a visible character | 146 |
| Print the last line when any row is non-empty (pyfiglet checks only the first row) | 71 |
| Keep the final newline when using `-s` | 869 |
| Flip without converting `_` to `-` | 393 |
| Centre using width 80 instead of `-w` | 319 |
| Ignore the font when resolving `-D auto` | 52 |
| Do not use spaces as wrapping break points | 456 |
| Cut only one end-mark character instead of up to two | 1890 |

Three additional planted bugs did not change the output for any input, because the shipped fonts never reach that code. Their details are documented in `NOTES.md`.

The secret from the practice task was also tested. The oracle's Go implementation successfully draws it inside the built Docker image.

Screenshots of the results are available in the [`screenshots/`](screenshots/) directory.

## Hand-in notes

### The most important lesson from the port

The biggest challenge was not implementing the six character-smushing rules themselves. It was preserving the internal state and handling the less obvious cases correctly.

One particularly important detail is what happens after wrapping. Pyfiglet does not reset `prevCharWidth` to zero. Instead, it retains the width of the character that did not fit on the previous line. Changing this behaviour causes 1,197 out of 2,000 cases to fail.

Right-to-left rendering also requires special handling. The meaning of the left and right sides inside `smushAmount` must be swapped when the direction changes. Missing this adjustment causes 787 test failures.

Some character combinations are much less common, such as `[]` becoming `|` and the special handling of `()` compared with `<>`. These cases are still covered by the hidden tests, even though they account for relatively few failures.

### Docker and verifier issues

None of the three Docker traps listed on the practice sheet was hit. The image used `golang:1.23-alpine` from the start (not `golang:1.23-bookworm`, which contains Python), installed Bash with `apk add bash` (Alpine has no Bash by default), and fetched pyfiglet from GitHub in stage 1 instead of copying it from the laptop.

The actual problem came from Harbor's verifier configuration. By default, the verifier runs using the same user as the Docker image's configured `USER`, which was `player` in this case.

This meant the agent's program could potentially access `/tests/data/hidden.jsonl` while being graded.

To prevent that, the verifier was configured to run as root using `user = "root"`. Access to `/tests` was then restricted to root, and the twin was executed as `nobody`.

## Docker environment (`environment/Dockerfile`)

The Docker image was set up to meet all six requirements from the practice task.

| Rule | Implementation |
|---|---|
| D1: Two-stage build | The `source` stage uses `alpine/git` to clone pyfiglet at the required commit. The final stage copies only `/src`. |
| D2: No Python | The final image uses `golang:1.23-alpine`. Running `command -v python3` confirms that Python is not installed. |
| D3: Project setup | The first stage performs the Makefile's `clean` and `minimal` setup by copying `pyfiglet/fonts-standard/*` into a newly created `pyfiglet/fonts/` directory. |
| D4: Normal user | The `player` user (UID 1000) owns `/workspace/repo`, and the image runs with `USER player`. |
| D5: Pinned images | Both images are pinned using their tags and SHA-256 digests. |
| D6: Bash | Bash is installed using `apk add bash`. |

The environment can be checked with:

```bash
docker build -t figlet-room environment/

docker run --rm figlet-room sh -c \
'whoami; pwd; ls pyfiglet/fonts | wc -l; command -v python3 || echo NO_PYTHON; command -v bash; touch x && echo CAN_WRITE'
```

## Grading setup (`tests/`)

The `test.sh` script starts the grader by running:

```bash
cd /tests && go run grade.go
```

The grader uses only the Go standard library and does not require network access.

The checks are divided into three parts:

| Check | Weight | Passing requirements |
|---|---:|---|
| `build` | 1 | Both `go build ./...` and `go build -o /tmp/figlet .` must succeed inside `/workspace/repo`. |
| `no_python` | 1 | The build must pass, there must be no `.py` files under `/workspace/repo`, and at least one hidden test must produce the correct output. |
| `behaviour` | 4 | Measures the share of the 2,000 hidden test cases whose standard output matches the expected `out` exactly. Each case has a five-second limit. |

The expected rewards are:

- Nothing implemented: `0`
- Build requirements only: `1/6`, approximately `0.17`
- Fully correct implementation: `1.0`

When the behaviour score reaches exactly `1.0`, the grader unlocks the secret challenge. It decodes `tests/secret.b64` and uses the twin to render the secret text with `-f slant`.

The resulting output is written after `*** SECRET UNLOCKED ***` in `verifier/test-stdout.txt`.

If the behaviour score is below `1.0`, the grader displays:

```text
No secret for you. Yet.
```

## Additional security improvements

Some extra precautions were added beyond the original practice requirements.

- **Run the verifier as root:** The configuration uses `[verifier] user = "root"`. Without this, the verifier inherits the image's `USER player`, potentially allowing the agent's program to read hidden test answers.
- **Clean up background processes:** Before grading begins, `test.sh` terminates every process left running by `player` and makes `/tests` accessible only to root.
- **Run the twin with restricted permissions:** The twin runs as `nobody` from `/`, so it cannot access the hidden answers or rely on the current working directory.
- **Keep Go builds isolated:** Builds use `GOPROXY=off`, `GOFLAGS=-mod=mod`, `GOWORK=off`, and `GOENV=off`, along with a fresh build cache. This ensures that the implementation uses only the Go standard library and cannot inherit settings from the agent's environment.

There is one remaining limitation with the shared-verifier setup. The tests are copied shortly before `test.sh` starts, leaving a small window in which a background process left by the agent could attempt to read them. Using a separate verifier container would close this gap, but that is left for a later lesson.

## Test case generation (`tests/gen.py`)

The test generator runs on the author's local machine, where the Step 1 pyfiglet checkout is available alongside this project at `../pyfiglet`, with the font setup already completed.

It uses `random.seed(7)` to generate two separate sets:

- 2,000 visible test cases.
- 2,000 different hidden test cases.

For each case, the expected `out` is collected by running the original `pyfiglet.main()` in a fresh process. Cases that cause pyfiglet to crash or hang are discarded and replaced.

### Test coverage

The generated cases cover a range of fonts, output widths, options, and text inputs.

**Fonts**

The main fonts are:

`standard`, `slant`, `small`, `big`, `mini`, `banner`, `shadow`, and `script`.

The `ivrit` font is also included in about 8% of cases (153 visible, 162 hidden). It is particularly important because its font header requests right-to-left output, making it useful for testing the behaviour of `-D auto`.

**Widths and options**

- Widths include `10`, `20`, `40`, `60`, `80`, and `120`, as well as the default width. Narrow widths are used more frequently.
- Every supported `-j` and `-D` value is tested, with right-to-left cases appearing more often.
- The flags `-r`, `-F`, `-s`, and `-n` are each enabled in approximately one out of every four cases.
- Option order is randomized.

**Text inputs**

The generator includes:

- Regular words and sentences.
- Rare character combinations documented in `NOTES.md`, including every pair of bracket classes in both orders.
- Special characters such as `| / \ _ [ ] { } ( ) < >`.
- Multiple consecutive spaces.
- Long sentences that require wrapping.
- Latin-1 characters.
- Characters missing from the selected font.
- Newline characters and empty text.
- Text split across multiple command-line arguments.

This provides coverage for both normal rendering and the less common edge cases that can easily be missed during a port.

## Project structure

The repository is organized as follows:

| Path | Purpose |
|---|---|
| `instruction.md` | Instructions provided to the agent. |
| `task.toml` | Harbor configuration, including the `player` agent user, root verifier user, timeouts, and `/workspace/repo` artifact. |
| `environment/Dockerfile` | Defines the two-stage Docker environment. |
| `solution/solve.sh` | Oracle implementation containing the complete Go port, with fonts embedded using `go:embed`. |
| `cheat/solve.sh` | Attempts to look up visible answers to demonstrate that the grader detects cheating. |
| `cheat/make_cheat.sh` | Regenerates `cheat/solve.sh` using `tests/data/visible.jsonl`. |
| `tests/test.sh` | Starts the verification process. |
| `tests/grade.go` | Implements the automated grader. |
| `tests/gen.py` | Generates test cases and expected outputs. |
| `tests/data/` | Stores the frozen test data. |
| `tests/secret.b64` | Contains the secret used when the implementation achieves a perfect score. |
| `tools/first_diffs.go` | Author-side utility for displaying the first N differences between outputs. |
| `NOTES.md` | Contains licensing details, setup instructions, smushing rules, and rare edge cases. |
| `screenshots/` | Terminal captures of the oracle, nop and cheat rewards. |

## Running the task

Run the following commands from the directory containing `figlet-go`:

```bash
harbor run -p ./figlet-go -a oracle

harbor run -p ./figlet-go -a nop
```

To test the cheat implementation, first make a backup of `solution/solve.sh`, replace it with `cheat/solve.sh`, and run the oracle command. Restore the original solution afterward.

On Windows, set `PYTHONUTF8=1` before running Harbor. Otherwise, Harbor may encounter problems when printing Unicode characters.
