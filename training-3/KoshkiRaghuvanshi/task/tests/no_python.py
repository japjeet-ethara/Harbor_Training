import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from rewardkit import criterion

from go_run import go, passes_behaviour


@criterion
def no_python(workspace: Path) -> float:
    has_python_source = any(
        ".py" in path.name.lower()
        for path in workspace.rglob("*")
        if path.is_file()
    )
    if has_python_source:
        return 0.0
    probe = go(
        workspace,
        """for interpreter in \\
            python python2 python3 python3.11 python3.12 \\
            /usr/local/bin/python /usr/local/bin/python2 \\
            /usr/local/bin/python3 /usr/local/bin/python3.11 \\
            /usr/local/bin/python3.12 /usr/bin/python /usr/bin/python2 \\
            /usr/bin/python3 /usr/bin/python3.11 /usr/bin/python3.12 \\
            /bin/python /bin/python2 /bin/python3; do
                if "$interpreter" -c 'raise SystemExit(0)' >/dev/null 2>&1; then
                    exit 1
                fi
            done
            exit 0""",
    )
    return (
        1.0
        if probe is not None
        and probe.returncode == 0
        and passes_behaviour(workspace)
        else 0.0
    )
