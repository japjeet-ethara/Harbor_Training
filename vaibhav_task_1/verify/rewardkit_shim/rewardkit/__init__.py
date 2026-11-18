"""Minimal OFFLINE stand-in for harbor-rewardkit, used only by
verify/run_local.sh when the real package cannot be downloaded.

It implements just what tests/checks/ uses, following the Reward Kit docs:
  * @criterion / @criterion(description=...) — first parameter is `workspace`;
    a criterion whose only parameter is `workspace` is called automatically;
    returns bool (-> 1.0/0.0) or float in [0, 1].
  * each .py file in the tests dir = one score named after the file
    (weighted mean of its criteria, weight default 1.0)
  * reward.toml [[reward]] with aggregation = "weighted-mean" and `weights`
  * writes reward.json and reward-details.json next to each other.
On a real Harbor run, test.sh uses the real package via uvx instead.
"""
import importlib.util
import inspect
import json
import math
import os
import sys
import tomllib
from pathlib import Path

_REGISTRY = []


def criterion(fn=None, *, description=None, shared=False):
    def wrap(f):
        _REGISTRY.append({"fn": f, "name": f.__name__,
                          "description": description or f.__name__})
        return f
    return wrap(fn) if fn is not None else wrap


def _score(value):
    if isinstance(value, dict):
        value = value["score"]
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    value = float(value)
    if math.isnan(value) or math.isinf(value):
        raise ValueError("criterion returned a non-finite score")
    return value


def run(tests_dir, workspace="/app", output="/logs/verifier/reward.json"):
    tests_dir = Path(tests_dir)
    workspace = Path(workspace)
    scores, details = {}, {}
    for path in sorted(tests_dir.glob("*.py")):
        _REGISTRY.clear()
        spec = importlib.util.spec_from_file_location(f"rk_check_{path.stem}", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        crits = []
        for c in list(_REGISTRY):
            params = list(inspect.signature(c["fn"]).parameters)
            if params == ["workspace"]:
                s = _score(c["fn"](workspace))
                crits.append({"name": c["name"], "description": c["description"],
                              "score": s, "weight": 1.0})
        if not crits:
            continue
        tw = sum(c["weight"] for c in crits)
        scores[path.stem] = sum(c["score"] * c["weight"] for c in crits) / tw
        details[path.stem] = crits
    cfg = {}
    if (tests_dir / "reward.toml").is_file():
        cfg = tomllib.loads((tests_dir / "reward.toml").read_text())
    rewards = cfg.get("reward") or [{"name": "reward", "aggregation": "weighted-mean", "weights": {}}]
    out = dict(scores)
    for rw in rewards:
        assert rw.get("aggregation", "weighted-mean") == "weighted-mean", "shim supports weighted-mean only"
        w = {k: float(rw.get("weights", {}).get(k, 1.0)) for k in scores}
        out[rw["name"]] = sum(scores[k] * w[k] for k in scores) / sum(w.values())
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(out, indent=2) + "\n")
    (output.parent / "reward-details.json").write_text(json.dumps(details, indent=2) + "\n")
    return out


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(prog="rewardkit (offline shim)")
    ap.add_argument("tests_dir")
    ap.add_argument("--workspace", default="/app")
    ap.add_argument("--output", default="/logs/verifier/reward.json")
    a = ap.parse_args(argv)
    run(a.tests_dir, a.workspace, a.output)


# Allow `import rewardkit as rk; rk.<criterion>` style access to registered names.
def __getattr__(name):
    for c in _REGISTRY:
        if c["name"] == name:
            return c["fn"]
    raise AttributeError(name)
