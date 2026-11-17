# Recorded commands and provenance

Paths denoted by `RUN` were fresh validation directories. The copied evidence retains the actual run identifiers.

## Sources

- Assignment PDF `04-harbor-day3.pdf`, section 18 on pages 18–24. SHA-256 `55d58acb4c1f560839ba60e1aec793c59539b9bccb4339e985ba2bf5801ec2d2`. The PDF supplied the assignment. User additions and workflow changes are recorded in `REQUIREMENTS.md`.
- Upstream clone and detached checkout using Git. `git log -1 --format='%H %cI'` recorded `42f43e2de55bf003b286c6f8e8d8b2d26676a167 2024-04-05T22:03:59-07:00`. The starter tree was extracted from `git archive --format=tar` at the pinned commit.
- Go 1.23.12 from the official Windows archive `go1.23.12.windows-amd64.zip`, validated against SHA-256 `07c35866cdd864b81bb6f1cfbf25ac7f87ddc3a976ede1bf5112acbb12dfe6dc`. [Official Go downloads](https://go.dev/dl/)
- The Docker Registry manifest endpoints supplied the digests in the two Dockerfiles. They resolve the original Go 1.23 tag and Python 3.12.14 slim Bookworm tag to fixed indexes.

## Reference and native builds

Run in the source task root. The executables were the recorded CPython bundle and pinned Go toolchain. Go commands set `GOENV=off GOTOOLCHAIN=local GOWORK=off GOPROXY=off CGO_ENABLED=0 GOTELEMETRY=off` and used workspace scratch caches.

```text
python tests/gen.py --output RUN/first
python tests/gen.py --output RUN/second
Get-FileHash RUN/first/*, RUN/second/*, RUN/first.json, RUN/second.json
go build -o RUN/titlecase.exe .                          [from solution/src]
python tools/validate_reference.py RUN/titlecase.exe --count 120000
go vet ./...                                            [from solution/src]
GOOS=linux GOARCH=amd64 go build -o RUN/titlecase-linux . [from solution/src]
python tools/generate_unicode.py RUN/python_tables.go
python tools/check_grader.py --go GO_1_23_12 --evidence RUN
```

Each generation command's stdout is in its JSON manifest. Full logs include an earlier failed apostrophe comparison and the successful correction. Git Bash could not initialize in the Windows sandbox. ShellCheck was used for Bash static analysis.

## Harbor and verifier

`harbor==0.26.0` and `harbor-rewardkit==0.2.4` were installed in a work-only Python environment. The verifier lock was generated with uv 0.11.11 using `uv pip compile rewardkit.in --python PYTHON_3_12_14 --python-platform x86_64-unknown-linux-gnu --generate-hashes --no-header --no-annotate --only-binary=:all: --output-file tests/requirements.lock`. The input was one line containing `harbor-rewardkit==0.2.4`. The shipped verifier uses the published Reward Kit package on Linux. See the individual log headers for the image-build and Harbor baseline commands.

`harbor lint TASK --select ALL --json` ran with Harbor 0.26.0. An earlier run found an unused root ignore file. That file was removed and the final lint run reported zero findings.

Native grader tests substitute direct Windows subprocesses for the Linux credentials, preflight, and container isolation. A separate Reward Kit compatibility run used the published Reward Kit package with import placeholders for unused POSIX worker interfaces. Its command was `python native-rewardkit-shim-*.py --go GO_1_23_12 --evidence RUN --rewardkit`. The adapter is included with its evidence and stays outside the verifier's Docker build context. The successful run retains the unmodified Reward Kit reward JSON for each scenario. The tests and images still require standalone Docker validation.
