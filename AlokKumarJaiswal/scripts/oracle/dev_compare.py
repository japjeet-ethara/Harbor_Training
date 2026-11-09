import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ORACLE = ROOT / "oracle_dev"
DATA = ROOT / "titlecase-go" / "tests" / "data"
INPUTS = DATA / "inputs.txt"
EXPECTED = DATA / "expected.txt"


def require(path: Path, directory: bool = False) -> None:
    if directory:
        ok = path.is_dir()
    else:
        ok = path.is_file()
    if not ok:
        raise SystemExit(f"abort: missing {path}")


def byte_lines(data: bytes) -> list[bytes]:
    if data.endswith(b"\n"):
        data = data[:-1]
    return data.split(b"\n")


def emit(data: bytes, stream) -> None:
    if not data:
        return
    stream.write(data)
    if not data.endswith(b"\n"):
        stream.write(b"\n")
    stream.flush()


def main() -> int:
    limit = 10
    if len(sys.argv) > 1:
        limit = int(sys.argv[1])

    require(ORACLE, directory=True)
    require(INPUTS)
    require(EXPECTED)

    oracle = ORACLE.resolve().as_posix()
    if not Path(oracle).is_absolute():
        raise SystemExit(f"abort: docker volume path is not absolute: {oracle}")
    build = subprocess.run(
        [
            "docker", "run", "--rm",
            "-v", f"{oracle}:/work",
            "-w", "/work",
            "-v", "gocache:/root/.cache/go-build",
            "golang:1.23",
            "go", "build", "-o", "/tmp/tc", ".",
        ],
        capture_output=True,
    )
    emit(build.stdout, sys.stdout.buffer)
    emit(build.stderr, sys.stderr.buffer)
    if build.returncode != 0:
        return build.returncode

    # --rm drops /tmp/tc with the build container. This second run compiles
    # again against the same cache volume, then reads stdin.
    with INPUTS.open("rb") as fh:
        run = subprocess.run(
            [
                "docker", "run", "--rm", "-i",
                "-v", f"{oracle}:/work",
                "-w", "/work",
                "-v", "gocache:/root/.cache/go-build",
                "golang:1.23",
                "sh", "-c", "go build -o /tmp/tc . && exec /tmp/tc",
            ],
            stdin=fh,
            capture_output=True,
        )
    if run.returncode != 0:
        emit(run.stderr, sys.stderr.buffer)
        return run.returncode

    inputs = byte_lines(INPUTS.read_bytes())
    expected = byte_lines(EXPECTED.read_bytes())
    actual = byte_lines(run.stdout)

    compared = max(len(expected), len(actual))
    equal = 0
    diffs = []
    for i in range(compared):
        exp = expected[i] if i < len(expected) else None
        act = actual[i] if i < len(actual) else None
        if exp == act:
            equal += 1
            continue
        if len(diffs) < limit:
            src = inputs[i] if i < len(inputs) else None
            diffs.append((i + 1, src, exp, act))

    print(f"lines compared: {compared}")
    print(f"lines equal: {equal}")
    print(f"lines different: {compared - equal}")
    for n, src, exp, act in diffs:
        print(n, ascii(src), ascii(exp), ascii(act))
    return 0


if __name__ == "__main__":
    sys.exit(main())
