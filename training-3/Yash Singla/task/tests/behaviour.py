from pathlib import Path
import re
import subprocess

from rewardkit import Worker, WorkerError, criterion


_AUDIT = Path("/usr/local/bin/titlecase-audit")
_DATA = Path("/tests/data")
_MIN_CATEGORY_CASES = 100
_MIN_CATEGORY_ACCURACY = 0.90
_FAILED_CATEGORY_SCORE_CAP = 0.19

# Score the special-rule families that are represented at scale in the fixed
# hidden exam. Some source templates (such as slash and apostrophe examples)
# are exhausted by the visible set, so categories without enough hidden cases
# are not treated as scored categories.
_SPECIAL_CATEGORIES = {
    "Mc prefixes": re.compile(r"(?i)(?<!\w)mc\w"),
    "hyphens and dashes": re.compile(r"[-–‒—―]"),
    "inline periods": re.compile(r"\w\.\w"),
    "all-caps lines": None,
    "leading honorifics": re.compile(r"(?i)^(?:mr|mrs|ms|dr)\b"),
    "punctuation subphrases": re.compile(r"[:.;?!\-–‒—―][ \t]"),
    "mixed-case names and acronyms": re.compile(r"(?<!\w)(?:[a-z][A-Z]|[A-Z]{2,})"),
    "outer punctuation": re.compile(r'''^[\(\["#]'''),
    "non-ASCII text": None,
    "significant whitespace": None,
    "digits and underscores": re.compile(r"[0-9_]"),
    "slashes": re.compile(r"/"),
    "apostrophes": re.compile(r"['‘’]"),
}


def _has_category(name: str, pattern: re.Pattern[str] | None, line: str) -> bool:
    if name == "all-caps lines":
        return line.isupper()
    if name == "non-ASCII text":
        return any(ord(char) > 127 for char in line)
    if name == "significant whitespace":
        return (
            "\t" in line
            or "\u00a0" in line
            or re.search(r" {2,}", line) is not None
            or line != line.strip()
        )
    assert pattern is not None
    return pattern.search(line) is not None


@criterion(
    description=(
        "Share of hidden title lines matching the original Python "
        "titlecase outputs exactly"
    )
)
def behaviour(workspace: Path) -> float:
    try:
        inputs = (_DATA / "hidden_inputs.txt").read_bytes()
        expected_bytes = (_DATA / "hidden_expected.txt").read_bytes()
    except OSError:
        return 0.0

    if not expected_bytes:
        return 0.0

    # Build and no-Python are prerequisites, not independent reward points.
    if any(
        path.is_file() and path.suffix == ".py"
        for path in workspace.rglob("*")
    ):
        return 0.0

    # This trusted, precompiled verifier binary parses every submitted Go file.
    # It runs before Worker and never executes submitted code.
    try:
        audit = subprocess.run(
            [str(_AUDIT), str(workspace)],
            cwd="/tmp",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return 0.0
    if audit.returncode != 0:
        return 0.0

    try:
        result = Worker(
            env={
                "PATH": "/usr/local/go/bin",
                "GOROOT": "/usr/local/go",
                "CGO_ENABLED": "0",
            }
        ).run(
            "GO111MODULE=off go build -o titlecase-bin . && exec ./titlecase-bin",
            files=list(workspace.iterdir()),
            stdin=inputs,
            timeout_sec=180,
        )
    except WorkerError:
        return 0.0
    # WorkerSetupError is intentionally allowed to propagate: it means
    # RewardKit could not establish or clean up its execution boundary.
    if result.returncode != 0:
        return 0.0

    input_lines = inputs.split(b"\n")
    expected = expected_bytes.split(b"\n")
    actual = result.stdout.split(b"\n")
    compared = max(len(actual), len(expected))
    if compared == 0:
        return 0.0

    matches = sum(left == right for left, right in zip(actual, expected))
    overall = matches / compared

    category_indices = {name: [] for name in _SPECIAL_CATEGORIES}
    for index, raw_line in enumerate(input_lines):
        if not raw_line:
            continue
        line = raw_line.decode("utf-8")
        for name, pattern in _SPECIAL_CATEGORIES.items():
            if _has_category(name, pattern, line):
                category_indices[name].append(index)

    for indices in category_indices.values():
        if len(indices) < _MIN_CATEGORY_CASES:
            continue
        category_matches = sum(
            index < len(actual)
            and index < len(expected)
            and actual[index] == expected[index]
            for index in indices
        )
        if category_matches / len(indices) < _MIN_CATEGORY_ACCURACY:
            return min(overall, _FAILED_CATEGORY_SCORE_CAP)

    return overall
