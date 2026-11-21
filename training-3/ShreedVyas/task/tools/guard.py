#!/usr/bin/env python3
"""Freeze and verify files so an AI editor cannot silently change a validated task.
  python tools/guard.py snapshot <task-folder>   # after oracle=1.0 / nop=0 / cheat<0.2
  python tools/guard.py verify   <task-folder>   # prints any file that changed; exit 1 if any
"""
import hashlib, json, sys
from pathlib import Path

mode, root = sys.argv[1], Path(sys.argv[2] if len(sys.argv) > 2 else ".").resolve()
SKIP = {"jobs", "__pycache__", ".git", "screenshots"}
store = root / ".guard.json"


def digest():
    out = {}
    for p in sorted(root.rglob("*")):
        rel = p.relative_to(root)
        if p.is_file() and not (set(rel.parts) & SKIP) and p.name != ".guard.json":
            out[rel.as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


if mode == "snapshot":
    store.write_text(json.dumps(digest(), indent=1))
    print(f"froze {len(json.loads(store.read_text()))} files -> {store}")
elif mode == "verify":
    old, new = json.loads(store.read_text()), digest()
    changed = [f for f in old if f in new and old[f] != new[f]]
    removed = [f for f in old if f not in new]
    added = [f for f in new if f not in old]
    for f in changed: print("CHANGED:", f)
    for f in removed: print("REMOVED:", f)
    for f in added: print("ADDED:  ", f)
    print("OK - nothing changed" if not (changed or removed or added) else "DIFFERENCES FOUND")
    sys.exit(1 if (changed or removed or added) else 0)
else:
    sys.exit("usage: guard.py snapshot|verify <task-folder>")
