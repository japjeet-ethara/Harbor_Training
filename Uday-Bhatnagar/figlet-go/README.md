# Harbor Practice 2: FIGlet Go port

This folder is the deliverable task. Nothing has been pushed to GitHub.

## What is included

- `NOTES.md`: pinned source, commit date, licensing, source-accurate rules and rare cases.
- `environment/Dockerfile`: two-stage build, pinned tags, prepared standard fonts, Alpine Go, bash, player uid 1000, no Python installation.
- `instruction.md` and `task.toml`: agent requirements and Harbor configuration.
- `tests/gen.py`, `tests/data/`: reproducible upstream-derived 2,000 visible and 2,000 hidden answers, with hashes.
- `tests/grade.go`, `tests/test.sh`, `tests/secret.b64`: offline Go grader and unlock message.
- `solution/solve.sh`: self-contained oracle installer; it writes all Go code, copies fonts, removes Python source, and builds. The accompanying Go module and font directory let you inspect/build the completed port directly.
- `cheat/solve.sh`: self-contained visible-answer lookup attempt; it never uses hidden answers.
- `tests/compare.py`: first-five visible differences helper.
- `validate.sh`, `tools/check_rewards.py`: run the three Harbor trials and assert real scores.
- `evidence/`: measured checks and explicit environment limitations.

## Validation actually completed

The port builds with Go 1.23.12. Using Go's JavaScript/WebAssembly target with Node, the same rendering and argument-handling code matched **4,000/4,000** frozen cases (2,000 each). The temporary batch harness changes only the top-level entry point and final output destination to capture results; it does not alter rendering, parsing, options, or font loading. This is a renderer validation, not a Harbor trial.

Reproduce that check with `python3 tools/verify_wasm.py` when Go 1.23 and Node are on PATH (or supply `--go PATH --node PATH`). The unmodified CLI was also compiled to WebAssembly and independently matched three sampled cases. Both secret banners were rendered by that unmodified CLI; their text captures are included. The Go grader also cross-compiles successfully for Linux amd64.

Generation was run twice and its SHA-256 hashes matched. All cases are unique within their split, with zero argument overlap between splits. Three independently launched original CLI cases matched the frozen bytes. Both splits contain 211 right-to-left cases at width 10 or 20. Two smushing examples were directly checked against upstream. The task TOML parses with the installed Harbor configuration model.

**Docker image build, six runtime checks, Harbor oracle/nop/cheat rewards, and real screenshots remain unverified.** Docker's Linux engine is unavailable; Docker Desktop startup reports a missing installation registry key. Windows Application Control blocks harbor.exe and the generated Windows Go executable. No screenshots or reward files have been fabricated. See `evidence/VALIDATION.md`.

## Run on a machine with working Docker and Harbor

From a Linux/macOS/WSL shell:

```bash
chmod +x validate.sh solution/solve.sh cheat/solve.sh tests/test.sh
./validate.sh
```

Expected scores by the specified formula are oracle **1.0**, nop **0.0**, cheat **1/6 = 0.1666666667**. These are expectations until the Harbor trials complete. The helper checks actual reward files and secret logs. Take genuine screenshots of the three terminal results after completion. The shared-verifier warning is expected for this exercise.

The Docker build context is `environment/`; it fetches the pinned upstream checkout itself. Only the Dockerfile is in that context, so grading data, solution and secret cannot be copied into the image.

## Regenerate answers

Clone https://github.com/pwaller/pyfiglet into a separate directory named `pyfiglet` beside this task folder, check out `255827efbc09d662875dad50fa0edc1e1263bf45`, and copy `pyfiglet/fonts-standard/*` into `pyfiglet/fonts/` within that checkout. Then run:

```bash
python3 tests/gen.py --source ../pyfiglet
```

The generator invokes the original main() with a binary stdout capture. It excludes glyphs at least as wide as the requested width: upstream raises on wider glyphs and loops forever on equal-width glyphs. It never manually supplies expected output.

## Build the completed port directly

```bash
cd solution
go build -o /tmp/figlet .
cd /tmp
./figlet -f slant hello
```

Fonts are embedded, so the executable is independent of the current working directory. The port uses the standard library only. License and original font notices are included.

## Reflection

The most delicate source rule was directional overlap: Big-X is asymmetric, and right-to-left universal smushing favors the later input glyph. All frozen cases passed the first executable comparison, so there is no honest claim of repeated smushing failures.

The Docker trap encountered here was environmental: Docker Desktop could not start its Linux engine. The supplied image avoids the exercise's two design traps by using Alpine to exclude Python and explicitly installing bash.

Publication is pending your explicit permission. This package intentionally contains no GitHub remote or push step.
