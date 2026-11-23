import argparse
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def prepare(destination):
    destination.mkdir(exist_ok=False, parents=True)
    for name in ("task.toml", "instruction.md"):
        shutil.copyfile(ROOT / name, destination / name)
    for name in ("environment", "tests"):
        shutil.copytree(ROOT / name, destination / name, ignore=shutil.ignore_patterns("__pycache__"))
    solution = destination / "solution"
    shutil.copytree(ROOT / "cheat/replay", solution / "replay")
    shutil.copyfile(ROOT / "cheat/solve.sh", solution / "solve.sh")
    shutil.copyfile(ROOT / "tests/data/expected.txt", solution / "visible-answers.txt")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("destination", type=Path)
    prepare(parser.parse_args().destination)
