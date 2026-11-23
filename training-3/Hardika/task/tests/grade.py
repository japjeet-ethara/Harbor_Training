import argparse
import json
import os
import shutil
import signal
import subprocess
import tempfile
from pathlib import Path

DATA = Path(__file__).resolve().parent / "data"
RECORDS = 2000
MAX_OUTPUT = 8 * 1024 * 1024
LINUX_GO = "/usr/local/go/bin/go"
NOBODY = 65534
GATE = 0.5


def frozen_records(data):
    if not data.endswith(b"\n"):
        raise ValueError("Frozen data must end with LF")
    records = data.split(b"\n")[:-1]
    if len(records) != RECORDS:
        raise ValueError(f"Expected {RECORDS} frozen records")
    return records


def share_correct(output, answers):
    rows = output.split(b"\n")
    if len(rows) > len(answers) + 1 or (len(rows) == len(answers) + 1 and rows[-1]):
        return 0.0
    return sum(actual == expected for actual, expected in zip(rows[:-1], answers)) / len(answers)


def contains_python(workspace):
    for root, dirs, files in os.walk(workspace, followlinks=False):
        if any(name.endswith(".py") for name in files):
            return True
        if any(name.endswith(".py") and (Path(root) / name).is_symlink() for name in dirs):
            return True
    return False


def run(command, *, workspace, environment, timeout, isolated, input_file=None, stdout=None):
    stderr = subprocess.DEVNULL if input_file else None
    if isolated:
        prefix = ["/usr/bin/setpriv", "--no-new-privs", "--reuid", str(NOBODY),
                  "--regid", str(NOBODY), "--clear-groups", "--"]
        if input_file:
            prefix += ["/usr/bin/prlimit", f"--fsize={MAX_OUTPUT}", "--"]
        command = prefix + command
    with subprocess.Popen(
        command, cwd=workspace, env=environment, stdin=input_file or subprocess.DEVNULL,
        stdout=stdout, stderr=stderr, start_new_session=isolated,
    ) as process:
        try:
            return process.wait(timeout=timeout) == 0
        except subprocess.TimeoutExpired:
            if not isolated:
                process.kill()
            return False
        finally:
            if isolated:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass


def measure(workspace, go, *, isolated):
    result = {"build": 0.0, "no_python": 0.0, "behaviour": 0.0}
    inputs = DATA / "hidden_inputs.txt"
    frozen_records(inputs.read_bytes())
    answers = frozen_records((DATA / "hidden_expected.txt").read_bytes())

    if not workspace.is_dir():
        return result
    no_python = not contains_python(workspace)
    if isolated:
        os.chown(workspace, 0, NOBODY)
        workspace.chmod(0o775)
    with tempfile.TemporaryDirectory(prefix="titlecase-run-") as directory:
        home = Path(directory)
        if isolated:
            os.chown(home, NOBODY, NOBODY)
            home.chmod(0o700)
        binary = home / ("titlecase.exe" if os.name == "nt" else "titlecase")
        environment = {
            "PATH": str(Path(go).parent) + os.pathsep + os.defpath,
            "HOME": str(home),
            "GOCACHE": str(home / "cache"),
            "GOMODCACHE": str(home / "modules"),
            "GOTOOLCHAIN": "local",
            "GOWORK": "off",
            "CGO_ENABLED": "0",
            "GOENV": "off",
            "GOPROXY": "off",
            "GOSUMDB": "off",
        }
        if os.name == "nt":
            for name in ("SystemRoot", "TEMP", "TMP"):
                environment[name] = os.environ[name]
        options = {"workspace": workspace, "environment": environment, "isolated": isolated}
        if not run([go, "build", "./..."], timeout=180, **options):
            return result

        result["build"] = 1.0
        result["no_python"] = float(no_python)
        if not run([go, "build", "-o", str(binary), "."], timeout=45, **options):
            return result

        with inputs.open("rb") as input_file, tempfile.TemporaryFile() as output:
            if run([str(binary)], input_file=input_file, stdout=output, timeout=45, **options):
                output.seek(0)
                data = output.read(MAX_OUTPUT + 1)
                if len(data) <= MAX_OUTPUT:
                    result["behaviour"] = share_correct(data, answers)
    return result


def grade(workspace, go, *, isolated):
    # build and no_python are earned only by a port that really works: a program that
    # compiles but gets fewer than GATE of the hidden titles right scores 0 on both.
    result = measure(workspace, go, isolated=isolated)
    if result["behaviour"] < GATE:
        result["build"] = 0.0
        result["no_python"] = 0.0
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, default=Path("/workspace/repo"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--go", default=LINUX_GO)
    parser.add_argument("--local", action="store_true")
    args = parser.parse_args()
    go = shutil.which(args.go)
    if not go:
        raise SystemExit(f"Go toolchain unavailable: {args.go}")
    results = grade(args.workspace.resolve(), go, isolated=not args.local)
    args.output.write_text(json.dumps(results) + "\n", encoding="ascii")
