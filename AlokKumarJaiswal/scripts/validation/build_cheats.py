# -*- coding: utf-8 -*-
"""Write cheat/*.sh. Reads tests data only; does not modify titlecase-go."""

import base64
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXPECTED_PATH = ROOT / "titlecase-go" / "tests" / "data" / "expected.txt"
CHEAT_DIR = ROOT / "cheat"


def require(path: Path) -> None:
    if not path.is_file():
        raise SystemExit(f"abort: missing {path}")

GO_MOD_DELIM = "GO_MOD_EOF"
GO_SRC_DELIM = "GO_SRC_EOF"
B64_ALPHABET = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=")

NAMES = ("cheatA_keep", "cheatA_del", "cheatB_keep", "cheatB_del")


def read_utf8_bytes(path: Path) -> bytes:
    data = path.read_bytes()
    data.decode("utf-8")
    return data


def assert_delim_absent(content: bytes, delim: str, label: str) -> None:
    token = delim.encode("ascii")
    assert token not in content, f"{delim} appears inside {label}"


def lf_text(lines: list[str]) -> bytes:
    data = ("\n".join(lines) + "\n").encode("utf-8")
    assert b"\r" not in data, "generated text contains a CR byte"
    return data


def go_mod_bytes() -> bytes:
    content = lf_text(["module cheat", "", "go 1.23"])
    assert b"require" not in content
    assert_delim_absent(content, GO_MOD_DELIM, "go.mod")
    return content


def cheat_a_main(expected: bytes) -> bytes:
    payload = base64.standard_b64encode(expected).decode("ascii")
    assert set(payload) <= B64_ALPHABET
    assert base64.standard_b64decode(payload) == expected
    content = lf_text(
        [
            "package main",
            "",
            "import (",
            '\t"encoding/base64"',
            '\t"os"',
            ")",
            "",
            "func main() {",
            f'\tconst payload = "{payload}"',
            "\tout, err := base64.StdEncoding.DecodeString(payload)",
            "\tif err != nil {",
            "\t\tos.Stderr.WriteString(err.Error())",
            "\t\tos.Exit(1)",
            "\t}",
            "\tif _, err = os.Stdout.Write(out); err != nil {",
            "\t\tos.Stderr.WriteString(err.Error())",
            "\t\tos.Exit(1)",
            "\t}",
            "}",
        ]
    )
    assert b"`" not in content, "cheat A uses a raw string literal"
    assert_delim_absent(content, GO_SRC_DELIM, "cheat A main.go")
    return content


def cheat_b_main() -> bytes:
    content = lf_text(
        [
            "package main",
            "",
            "import (",
            '\t"io"',
            '\t"os"',
            ")",
            "",
            "func main() {",
            "\tif _, err := io.Copy(os.Stdout, os.Stdin); err != nil {",
            "\t\tos.Stderr.WriteString(err.Error())",
            "\t\tos.Exit(1)",
            "\t}",
            "}",
        ]
    )
    assert b"`" not in content, "cheat B uses a raw string literal"
    assert_delim_absent(content, GO_SRC_DELIM, "cheat B main.go")
    return content


def render_script(name: str, go_mod: bytes, main_go: bytes, delete_py: bool) -> bytes:
    assert_delim_absent(go_mod, GO_MOD_DELIM, f"{name} go.mod")
    assert_delim_absent(main_go, GO_SRC_DELIM, f"{name} main.go")
    parts = [
        b"#!/bin/bash\n",
        b"set -euo pipefail\n",
        b"\n",
        b"cd /workspace/repo\n",
        b"\n",
        f"cat > go.mod <<'{GO_MOD_DELIM}'\n".encode("ascii"),
        go_mod,
        f"{GO_MOD_DELIM}\n".encode("ascii"),
        b"\n",
        f"cat > main.go <<'{GO_SRC_DELIM}'\n".encode("ascii"),
        main_go,
        f"{GO_SRC_DELIM}\n".encode("ascii"),
        b"\n",
    ]
    if delete_py:
        parts.append(b"find /workspace/repo -type f -iname '*.py' -delete\n")
        parts.append(b"\n")
    parts.append(b"go build ./...\n")
    parts.append(f'echo "{name}"\n'.encode("ascii"))
    script = b"".join(parts)
    assert b"\r" not in script, f"{name}.sh contains a CR byte"
    script.decode("utf-8")
    return script


def main() -> None:
    require(EXPECTED_PATH)
    expected = read_utf8_bytes(EXPECTED_PATH)
    go_mod = go_mod_bytes()
    main_a = cheat_a_main(expected)
    main_b = cheat_b_main()
    scripts = {
        "cheatA_keep": render_script("cheatA_keep", go_mod, main_a, False),
        "cheatA_del": render_script("cheatA_del", go_mod, main_a, True),
        "cheatB_keep": render_script("cheatB_keep", go_mod, main_b, False),
        "cheatB_del": render_script("cheatB_del", go_mod, main_b, True),
    }
    assert tuple(scripts) == NAMES

    CHEAT_DIR.mkdir(parents=True, exist_ok=True)
    for name, script in scripts.items():
        path = CHEAT_DIR / f"{name}.sh"
        with path.open("wb") as handle:
            handle.write(script)
        written = path.read_bytes()
        assert written == script
        assert b"\r" not in written
        written.decode("utf-8")
        print(f"{path.name} {len(written)}")


if __name__ == "__main__":
    main()
