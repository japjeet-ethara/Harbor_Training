# -*- coding: utf-8 -*-
"""Write titlecase-go/solution/solve.sh from oracle_dev sources.

Reads oracle_dev/go.mod and oracle_dev/main.go as UTF-8 bytes. Backs up the
existing solution script, then writes solve.sh in binary with LF line endings.
Does not read or write titlecase-go/environment/repo.
"""

import hashlib
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GO_MOD_PATH = ROOT / "oracle_dev" / "go.mod"
MAIN_GO_PATH = ROOT / "oracle_dev" / "main.go"
SOLVE_PATH = ROOT / "titlecase-go" / "solution" / "solve.sh"
BACKUP_PATH = ROOT / "solution_backup" / "solve.sh.orig"


def require(path: Path) -> None:
    if not path.is_file():
        raise SystemExit(f"abort: missing {path}")


GO_MOD_DELIM = "GO_MOD_EOF"
GO_SRC_DELIM = "GO_SRC_EOF"


def read_utf8_source(path: Path, delimiter: str) -> bytes:
    """Return the file's raw bytes after the pre-write checks."""
    data = path.read_bytes()
    data.decode("utf-8")
    wrapped = delimiter.encode("ascii")
    assert wrapped not in data, f"{delimiter} appears inside {path.as_posix()}"
    assert b"\r" not in data, f"{path.as_posix()} contains a CR byte"
    assert data.endswith(b"\n"), f"{path.as_posix()} does not end with a newline"
    return data


def render_solve(go_mod: bytes, main_go: bytes) -> bytes:
    script = b"".join(
        [
            b"#!/bin/bash\n",
            b"set -euo pipefail\n",
            b"\n",
            b"cd /workspace/repo\n",
            b"\n",
            b"cat > go.mod <<'GO_MOD_EOF'\n",
            go_mod,
            b"GO_MOD_EOF\n",
            b"\n",
            b"cat > main.go <<'GO_SRC_EOF'\n",
            main_go,
            b"GO_SRC_EOF\n",
            b"\n",
            b"find /workspace/repo -type f -iname '*.py' -delete\n",
            b"\n",
            b"go build ./...\n",
            b'echo "titlecase-go solution built successfully"\n',
        ]
    )
    assert b"\r" not in script, "generated solve.sh contains a CR byte"
    return script


def main() -> None:
    require(GO_MOD_PATH)
    require(MAIN_GO_PATH)
    require(SOLVE_PATH)
    go_mod = read_utf8_source(GO_MOD_PATH, GO_MOD_DELIM)
    main_go = read_utf8_source(MAIN_GO_PATH, GO_SRC_DELIM)
    script = render_solve(go_mod, main_go)

    BACKUP_PATH.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SOLVE_PATH, BACKUP_PATH)

    with SOLVE_PATH.open("wb") as handle:
        handle.write(script)

    written = SOLVE_PATH.read_bytes()
    assert written == script
    assert b"\r" not in written
    print(f"bytes {len(written)}")
    print(f"sha256 {hashlib.sha256(written).hexdigest()}")


if __name__ == "__main__":
    main()
