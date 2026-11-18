# Harbor Task 1: titlecase to Go

Author: Komal. Created with AI assistance. This is the titlecase assignment in section 18 of `04-harbor-day3.pdf`.

The task is in `titlecase-go/`. Its starting candidate repository is `/workspace/repo`; the oracle installs a fresh Go implementation with a small pattern virtual machine. Only the Go standard library is used by that implementation. The full authoring bundle includes Python corpus generators and verifier tooling outside the completed candidate repository.

The reference is [python-titlecase](https://github.com/ppannuto/python-titlecase/tree/42f43e2de55bf003b286c6f8e8d8b2d26676a167), commit `42f43e2de55bf003b286c6f8e8d8b2d26676a167`. Reference execution uses CPython 3.12.8, Unicode 15.0.0, with optional `regex` absent. The default function is the oracle, rather than its CLI, callbacks, or configurable options.

See `VALIDATION.md` for measured results and genuine raw evidence. `ACCEPTANCE.md` maps requirements to implementation and checks. `NOTES.md` contains reference-checked examples, `PATTERN_ENGINE.md` describes the interpreter, and `DATASET.md` explains corpus coverage and reproducibility. Beginner setup is in `WINDOWS_WSL.md`.

## Run

From WSL or Linux, with Docker and Harbor 0.26.0 available:

```sh
harbor lint titlecase-go --select ALL --json
harbor run -p ./titlecase-go -a oracle
harbor run -p ./titlecase-go -a nop
bash tools/harbor_runs.sh
```

The last command runs all three baselines and saves a new dated evidence directory. It makes the replay task in a temporary directory and does not replace the real solution. RewardKit 0.2.4 and its dependencies are preinstalled in the separate verifier image from `tests/requirements.lock`. Runtime network access is disabled in both environments.

For independent reproducibility and differential validation:

```sh
docker build -f tools/Dockerfile.validation -t komal-titlecase-validation .
docker run --rm -v "$PWD:/project" komal-titlecase-validation python tools/verify.py
docker run --rm -v "$PWD:/project" komal-titlecase-validation python tools/test_grader.py
```

The standalone environment build is:

```sh
docker build -t komal-titlecase-agent titlecase-go/environment
docker run --rm komal-titlecase-agent sh -c 'pwd; ls -la; python --version; go version'
```

Run the Go source locally with `cd titlecase-go/solution && go run .`. The container toolchain is Go 1.23.12. A host Go installation is not required for Harbor or the validation container.

## Bundle boundaries

`environment/` contains only the pinned original source and upstream notices, plus the starting Dockerfile. `solution/` contains the Go port, tests, generated compatibility tables, and installer. `tests/` is private to the verifier, including both frozen corpora and the independent grader. `cheat/` contains only the visible-answer replay installer and its frozen output. Never distribute the complete authoring bundle into an agent container.

No repository was pushed or published. No model-agent attempt beyond oracle, nop, and replay is claimed. The local namespace `komal/titlecase-go` and Go module `komal/titlecase` are package identifiers, not GitHub account assertions.
