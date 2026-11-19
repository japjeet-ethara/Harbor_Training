# Security Review: titlecase-go

## Scope

Read-only review of the Harbor verifier, behavior check, task instructions, and
the recorded cheat baseline. Hidden test contents are not included here. The
required Reward Kit weights remain unchanged at behaviour 4, build 1, and
no_python 1.

## Findings

| # | Severity | Location | Finding |
|---|---|---|---|
| 1 | High | `tests/behaviour/check.py:34-42`; `tests/Dockerfile:14` | The submitted executable runs in the verifier container, which contains `/tests`. It runs with the verifier's root identity and can read hidden verifier files. Separate verifier mode isolates the agent from the verifier, not the executable from the verifier filesystem. |
| 2 | Medium | `tests/behaviour/check.py:48-53` | `splitlines()` removes line-ending distinctions, and `zip()` ignores extra output lines. The current comparison therefore does not enforce byte-for-byte output and can over-score output with extra lines. |
| 3 | Task integrity | `solution/solve.sh`; `cheat/solve.sh` | At review time, these separate files were byte-for-byte identical. The solution script wrote a Go program that replays the public expected file rather than porting titlecase. Restore the genuine solution before using an Oracle run to validate it. |

## Cheat Baseline

The cheat program copies `/tests/data/expected.txt` to stdout and ignores stdin.
It passes the build check because it writes a valid Go module and program. It
passes no_python because it deletes `.py` files and the build succeeds. It fails
the recorded hidden behavior check, yielding scores of 0 for behaviour, 1 for
build, and 1 for no_python. Under the required 4:1:1 weighted mean, the overall
reward is 0.3333. This partial score is consistent with the task's grading
instructions and does not by itself indicate a scoring defect.

The stronger concern is that the executable can read the hidden expected file
from its shared verifier filesystem and could bypass the behavior requirement.
The verifier image's test files were readable by the root process used to run
the program.

## Recommended Remediation

### Smallest practical file-access isolation

Keep the verifier as the trusted process that reads hidden inputs and expected
outputs. Make the entire `/tests` tree accessible only to root, then execute
the submitted binary as an unprivileged UID/GID with no supplementary groups.
Pass input only through stdin, capture stdout, and close other file descriptors.
Ensure the temporary executable and its parent directory are readable and
executable by that UID. Add `no-new-privileges` hardening if supported by the
verifier's Compose configuration.

This works inside Docker Desktop's Linux containers without a Docker socket.
It protects the test files through normal Linux permissions, but remains a
same-kernel boundary and must be configured carefully.

### Stronger runner-container isolation

For a stronger filesystem boundary, use a Harbor-recognized
`tests/docker-compose.yaml` with a trusted verifier service and a runner service.
Keep hidden tests only in the verifier service. Share only the submitted
workspace with the runner, preferably read-only; do not mount `/tests`, verifier
logs, or other test paths into it. Send test bytes over a restricted internal
channel; the runner supplies them to the executable's stdin and returns raw
stdout and exit status. The verifier retains expected bytes and computes the
partial score. Do not mount the Docker socket or expose runner ports to the
host. Compose services and volumes work with Docker Desktop in Linux-container
mode; the containers still share a kernel, and the bridge must be restricted.

Chroot or bubblewrap can also hide `/tests`, but require careful privilege
dropping and filesystem setup; bubblewrap's user-namespace requirements may not
be available inside Docker Desktop. A temporary directory alone is not
isolation.

### Byte-accurate partial scoring

Compare byte records while retaining line terminators. Count missing records as
mismatches and include extra records in the denominator (for example, using a
length-aware comparison rather than `zip()` alone). This preserves partial
credit while detecting incorrect bytes, line endings, missing lines, and extra
lines.

## Files Likely to Change

For the smaller permission-based fix: `tests/Dockerfile` and
`tests/behaviour/check.py`; optionally add `tests/docker-compose.yaml` for
container security options.

For the runner-container approach: add `tests/docker-compose.yaml`, a runner
image and runner service implementation, and update
`tests/behaviour/check.py` to use the restricted input/output channel.

Neither approach requires changing `tests/reward.toml`, the 4:1:1 weights, or
the hidden datasets.
