import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
go_src = root / "solution" / "src"
data = root / "tests" / "data"


def check(name_in: str, name_out: str) -> int:
    payload = (data / name_in).read_bytes()
    proc = subprocess.run(
        [
            "docker", "run", "--rm", "-i",
            "-v", f"{go_src}:/src",
            "-w", "/src",
            "golang:1.23",
            "go", "run", ".",
        ],
        input=payload,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr.decode("utf-8", "replace"))
        return 1
    actual = proc.stdout.decode("utf-8").splitlines()
    expected = (data / name_out).read_text(encoding="utf-8").splitlines()
    bad = 0
    if len(actual) != len(expected):
        print(f"{name_in}: count go={len(actual)} expected={len(expected)}")
    for i, exp in enumerate(expected):
        got = actual[i] if i < len(actual) else "<missing>"
        if got != exp:
            bad += 1
            if bad <= 15:
                src_line = (data / name_in).read_text(encoding="utf-8").splitlines()[i]
                print("---", name_in, i)
                print("IN ", src_line)
                print("EXP", exp)
                print("GO ", got)
    print(f"{name_in}: mismatches={bad}/{len(expected)}")
    return bad


def main() -> None:
    bad = check("inputs.txt", "expected.txt")
    bad += check("hidden_inputs.txt", "hidden_expected.txt")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
