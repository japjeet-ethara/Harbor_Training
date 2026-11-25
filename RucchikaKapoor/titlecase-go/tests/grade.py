#!/usr/bin/env python3
"""Verify the Go solution and score behavior in an isolated runtime."""
import json
import os
import resource
import shutil
import signal
import subprocess
import tempfile
from pathlib import Path

REPO = Path("/workspace/repo")
DATA = Path(__file__).resolve().parent / "data"
OUT = Path("/logs/verifier")
EXECUTION_TIMEOUT = 300
MIN_BEHAVIOR_SCORE = 0.2
MAX_OUTPUT_BYTES = 16 * 1024 * 1024


def go_env():
    env = os.environ.copy()
    env.update({
        "CGO_ENABLED": "0",
        "GOTOOLCHAIN": "local",
        "GOPROXY": "off",
        "GOSUMDB": "off",
    })
    return env


def run_build(args, **kwargs):
    return subprocess.run(
        args,
        cwd=REPO,
        env=go_env(),
        capture_output=True,
        timeout=EXECUTION_TIMEOUT,
        **kwargs,
    )


def check_build():
    try:
        result = run_build(["go", "build", "./..."])
    except (OSError, subprocess.TimeoutExpired) as exc:
        print(f"Go build could not run: {exc}")
        return False
    if result.returncode:
        print("go build ./... failed.")
        print(result.stderr.decode("utf-8", errors="replace"))
    return result.returncode == 0


def check_no_python(build_ok):
    if not build_ok:
        return False
    offenders = [
        path
        for path in REPO.rglob("*")
        if path.is_file() and path.suffix.lower() == ".py"
    ]
    if offenders:
        print("Python files remain in the submitted repository:")
        print("\n".join(str(path) for path in offenders))
        return False
    return True


def set_runtime_limits():
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(
        resource.RLIMIT_CPU,
        (EXECUTION_TIMEOUT, EXECUTION_TIMEOUT + 1),
    )
    resource.setrlimit(resource.RLIMIT_NPROC, (32, 32))
    resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
    resource.setrlimit(
        resource.RLIMIT_FSIZE,
        (MAX_OUTPUT_BYTES, MAX_OUTPUT_BYTES),
    )


def _read_limited_output(path):
    if path.stat().st_size >= MAX_OUTPUT_BYTES:
        print("Isolated program exceeded the output-size limit.")
        return None
    return path.read_bytes()


def _split_records(data):
    if not data:
        return []
    if data.endswith(b"\n"):
        data = data[:-1]
    return data.split(b"\n")


def run_in_jail(jail, binary_name, input_bytes):
    chroot = shutil.which("chroot") or "/usr/sbin/chroot"
    if not os.path.isfile(chroot):
        print(f"Isolation setup error: chroot was not found at {chroot}.")
        return None
    if os.geteuid() != 0:
        print("Isolation setup error: verifier must be root to create the chroot.")
        return None
    command = [
        chroot,
        "--userspec=65534:65534",
        "--groups=",
        str(jail),
        f"/{binary_name}",
    ]
    stdout_path = jail.parent / "program.stdout"
    stderr_path = jail.parent / "program.stderr"
    try:
        with stdout_path.open("wb") as stdout_file, stderr_path.open("wb") as stderr_file:
            process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=stdout_file,
                stderr=stderr_file,
                env={},
                cwd="/",
                close_fds=True,
                start_new_session=True,
                preexec_fn=set_runtime_limits,
            )
            try:
                process.communicate(input_bytes, timeout=EXECUTION_TIMEOUT)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.communicate()
                print("Isolated program exceeded the behavior check timeout.")
                return None
        output = _read_limited_output(stdout_path)
        error = _read_limited_output(stderr_path)
        if output is None or error is None:
            return None
        return subprocess.CompletedProcess(command, process.returncode, output, error)
    except (OSError, subprocess.SubprocessError, subprocess.TimeoutExpired) as exc:
        print(f"Isolated execution failed: {exc}")
        return None


def check_behavior(build_ok, no_python_ok):
    if not build_ok or not no_python_ok:
        return 0.0
    try:
        input_bytes = (DATA / "hidden_inputs.txt").read_bytes()
        expected_bytes = (DATA / "hidden_expected.txt").read_bytes()
    except OSError as exc:
        print(f"Could not read verifier fixtures: {exc}")
        return 0.0

    inputs = _split_records(input_bytes)
    expected = _split_records(expected_bytes)
    if not inputs or len(inputs) != len(expected):
        print("Verifier fixtures are empty or have mismatched record counts.")
        return 0.0

    try:
        with tempfile.TemporaryDirectory(prefix="titlecase-jail-") as temp_dir:
            jail_parent = Path(temp_dir)
            jail = jail_parent / "root"
            jail.mkdir(mode=0o755)
            jail_parent.chmod(0o755)
            jail.chmod(0o755)
            binary = jail / "titlecase"
            build = run_build(["go", "build", "-o", str(binary), "."])
            if build.returncode:
                print("Could not build the root Go program for the behavior check.")
                print(build.stderr.decode("utf-8", errors="replace"))
                return 0.0
            binary.chmod(0o755)
            result = run_in_jail(jail, binary.name, input_bytes)
            if result is None:
                return 0.0
    except (OSError, subprocess.TimeoutExpired) as exc:
        print(f"Verifier setup failed: {exc}")
        return 0.0

    if result.returncode:
        print("Isolated Go program returned a non-zero exit status.")
        print(result.stderr.decode("utf-8", errors="replace"))
        return 0.0

    actual = _split_records(result.stdout)
    if len(actual) != len(expected):
        print(
            f"Program emitted {len(actual)} records; expected exactly "
            f"{len(expected)}."
        )
        return 0.0
    matches = sum(got == want for got, want in zip(actual, expected))
    return matches / len(expected)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    build_ok = check_build()
    no_python_ok = check_no_python(build_ok)
    behavior = check_behavior(build_ok, no_python_ok)
    scores = {
        "build": 1.0 if build_ok else 0.0,
        "no_python": 1.0 if no_python_ok else 0.0,
        "behaviour": behavior,
        "reward": (
            behavior
            if build_ok and no_python_ok and behavior >= MIN_BEHAVIOR_SCORE
            else 0.0
        ),
    }
    reward_path = OUT / "reward.json"
    reward_path.write_text(json.dumps(scores, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(scores, indent=2))


if __name__ == "__main__":
    main()
