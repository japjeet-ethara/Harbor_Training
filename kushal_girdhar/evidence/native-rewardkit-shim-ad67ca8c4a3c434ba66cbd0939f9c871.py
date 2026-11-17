import os
from pathlib import Path
import runpy
import sys
from types import ModuleType

for name in ("grp", "pwd"):
    sys.modules[name] = ModuleType(name)
for name in ("O_DIRECTORY", "O_NOFOLLOW", "O_CLOEXEC"):
    if not hasattr(os, name):
        setattr(os, name, 0)
script = Path("work/kushal-titlecase-go/tools/check_grader.py").resolve()
sys.path.insert(0, str(script.parent))
sys.argv[0] = str(script)
print("Windows compatibility shim: import placeholders for unused POSIX worker primitives", flush=True)
runpy.run_path(str(script), run_name="__main__")
