import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rewardkit import criterion

from support import HIDDEN_RECORD_COUNT, RUN_TIMEOUT_SEC, log, records, run_command

HIDDEN_INPUTS = Path("/tests/data/hidden_inputs.txt")
HIDDEN_EXPECTED = Path("/tests/data/hidden_expected.txt")


def _fraction(matches: int) -> float:
    return matches / HIDDEN_RECORD_COUNT


@criterion
def behaviour(workspace: Path) -> dict[str, object]:
    if not workspace.is_dir():
        reason = f"workspace is not a directory: {workspace}"
        log(f"behaviour: {reason}")
        return {"score": 0.0, "reasoning": reason}

    try:
        expected = records(HIDDEN_EXPECTED.read_bytes())
        program_input = HIDDEN_INPUTS.read_bytes()
    except OSError as exc:
        reason = f"could not read hidden grading files: {exc}"
        log(f"behaviour: {reason}")
        return {"score": 0.0, "reasoning": reason}

    if len(expected) != HIDDEN_RECORD_COUNT:
        reason = f"hidden expected file has {len(expected)} records, not {HIDDEN_RECORD_COUNT}"
        log(f"behaviour: {reason}")
        return {"score": 0.0, "reasoning": reason}

    with tempfile.TemporaryDirectory(prefix="titlecase-grade-") as temp_dir:
        binary = str(Path(temp_dir) / "titlecase")
        code, _stdout, stderr, timed_out = run_command(
            ["go", "build", "-o", binary, "."],
            workspace,
            RUN_TIMEOUT_SEC,
        )
        if timed_out or code != 0:
            detail = stderr.decode("utf-8", errors="replace").strip()
            reason = (
                f"go build -o <temp> . timed out after {RUN_TIMEOUT_SEC}s"
                if timed_out
                else detail or f"go build -o <temp> . exited {code}"
            )
            log(f"behaviour: {reason}")
            return {"score": 0.0, "reasoning": reason}

        code, stdout, stderr, timed_out = run_command(
            [binary],
            workspace,
            RUN_TIMEOUT_SEC,
            stdin=program_input,
        )

    actual = records(stdout)
    matches = sum(
        1
        for index in range(HIDDEN_RECORD_COUNT)
        if index < len(actual) and actual[index] == expected[index]
    )
    score = _fraction(matches)
    contract_ok = code == 0 and not timed_out and len(actual) == HIDDEN_RECORD_COUNT
    if score == 1.0 and not contract_ok:
        score = _fraction(HIDDEN_RECORD_COUNT - 1)

    reason = (
        f"matches={matches}/{HIDDEN_RECORD_COUNT} "
        f"actual_records={len(actual)} exit={code} timed_out={timed_out}"
    )
    if stderr:
        diagnostic = stderr.decode("utf-8", errors="replace").strip()
        if diagnostic:
            reason = f"{reason}; stderr={diagnostic[:500]}"
    log(f"behaviour: {reason}")
    return {"score": score, "reasoning": reason}
