import json
import sys
from pathlib import Path


def check(jobs):
    dimensions = ("build", "no_python", "behaviour")
    cases = {
        "oracle": (1.0, 1.0, 1.0),
        "nop": (0.0, 0.0, 0.0),
        "replay": (1.0, 0.0, 0.0),
    }
    for name, components in cases.items():
        directory = jobs / name
        files = list(directory.glob("*/verifier/reward.json"))
        if len(files) != 1:
            raise SystemExit(f"Expected one Harbor trial reward for {name}; found {len(files)}.")
        path = files[0]
        data = json.loads(path.read_text(encoding="utf-8"))
        reward = data["reward"]
        meets_target = 0 <= reward < 0.2 if name == "replay" else reward == components[0]
        if not meets_target or tuple(data.get(key) for key in dimensions) != components:
            raise SystemExit(f"Unexpected reward in {path}: {data}")
        print(f"{name} reward={reward} source={path}")


if __name__ == "__main__":
    check(Path(sys.argv[1]))
