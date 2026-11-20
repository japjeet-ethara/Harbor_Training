from pathlib import Path
import re

from rewardkit import criterion

REPO_DIR = Path("/workspace/repo")
FORBIDDEN_GO_MARKERS = (
    b'"os/exec"', b'`os/exec`',
    b'"syscall"', b'`syscall`',
    b'"plugin"', b'`plugin`',
    b'"unsafe"', b'`unsafe`',
    b"os.StartProcess", b"ForkExec",
)

GO_COMMENT = rb"(?://[^\n]*|/\*[\s\S]*?\*/)"
GO_STRING = rb'(?:"(?:\\.|[^"\\\r\n])*"|`[^`]*`)'
GO_TRIVIA = rb"(?:\s|" + GO_COMMENT + rb")*"
GO_ALIAS = rb"(?:(?:[^\W\d]\w*|\.)" + GO_TRIVIA + rb")?"
CGO_PATH = rb'(?:"C"|`C`)'
GO_IMPORT_ENTRY = GO_ALIAS + GO_STRING
CGO_IMPORT = re.compile(
    rb"(?P<cgo>\bimport\b" + GO_TRIVIA
    + rb"(?:" + GO_ALIAS + CGO_PATH
    + rb"|\(" + GO_TRIVIA
    + rb"(?:" + GO_IMPORT_ENTRY + GO_TRIVIA + rb";?" + GO_TRIVIA + rb")*"
    + GO_ALIAS + CGO_PATH + rb"))"
    + rb"|" + GO_COMMENT + rb"|" + GO_STRING
    + rb"|'(?:\\.|[^'\\\r\n])*'"
)


@criterion
def check_no_python(workspace: Path) -> float:
    from behaviour import score_behaviour

    repo_path = REPO_DIR if REPO_DIR.exists() else workspace

    try:
        for path in repo_path.rglob("*"):
            if path.suffix == ".py":
                return 0.0
            if not path.is_file():
                continue
            with path.open("rb") as source:
                if source.read(4).startswith((b"#!", b"\x7fELF")):
                    return 0.0
                if path.suffix == ".go":
                    source.seek(0)
                    contents = source.read()
                    if any(marker in contents for marker in FORBIDDEN_GO_MARKERS):
                        return 0.0
                    if any(match.group("cgo") for match in CGO_IMPORT.finditer(contents)):
                        return 0.0
    except OSError:
        return 0.0

    return float(score_behaviour(workspace) >= 0.9)
