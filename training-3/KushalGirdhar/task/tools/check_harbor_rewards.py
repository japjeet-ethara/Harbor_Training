import argparse
import json
import math
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("jobs", type=Path)
    args = parser.parse_args()
    limits = {
        "oracle": lambda value: math.isclose(value, 1.0),
        "nop": lambda value: math.isclose(value, 0.0),
        "replay": lambda value: 0 <= value < 0.2,
    }
    for job, accepted in limits.items():
        files = list((args.jobs / job).glob("*/verifier/reward.json"))
        if len(files) != 1:
            raise RuntimeError(f"{job} produced {len(files)} reward files")
        reward = json.loads(files[0].read_bytes())["reward"]
        print(f"{job} = {reward!r} [{files[0]}]")
        if not accepted(reward):
            raise RuntimeError(f"{job} did not meet its score target")


if __name__ == "__main__":
    main()
