import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rewardkit import criterion

from support import (
    EXAM_RECORD_COUNT,
    RUN_TIMEOUT_SEC,
    go_build_all,
    log,
    python_files,
    records,
    run_command,
    run_submission,
)

# The graded exam. practice_inputs.txt and practice_expected.txt are the
# visible practice set and are not graded.
EXAM_INPUTS = Path("/tests/data/inputs.txt")
EXAM_ANSWERS = Path("/tests/data/answers.txt")


def _fraction(matches: int) -> float:
    return matches / EXAM_RECORD_COUNT


@criterion
def behaviour(workspace: Path) -> dict[str, object]:
    if not workspace.is_dir():
        reason = f"workspace is not a directory: {workspace}"
        log(f"behaviour: {reason}")
        return {"score": 0.0, "reasoning": reason}

    # Required conditions: behaviour, and so the reward, is 0 unless the
    # build and no_python conditions both pass.
    ok, detail = go_build_all(workspace)
    if not ok:
        reason = f"required condition failed: build: {detail}"
        log(f"behaviour: {reason}")
        return {"score": 0.0, "reasoning": reason}
    leftovers = python_files(workspace)
    if leftovers:
        reason = f"required condition failed: no_python: {len(leftovers)} .py file(s) remain"
        log(f"behaviour: {reason}")
        return {"score": 0.0, "reasoning": reason}

    try:
        expected = records(EXAM_ANSWERS.read_bytes())
        program_input = EXAM_INPUTS.read_bytes()
    except OSError as exc:
        reason = f"could not read exam files: {exc}"
        log(f"behaviour: {reason}")
        return {"score": 0.0, "reasoning": reason}

    # Inputs and answers are paired by line number, so both must hold exactly
    # EXAM_RECORD_COUNT records.
    input_count = len(records(program_input))
    if input_count != EXAM_RECORD_COUNT or len(expected) != EXAM_RECORD_COUNT:
        reason = (
            f"exam files have {input_count} inputs and {len(expected)} answers, "
            f"expected {EXAM_RECORD_COUNT} of each"
        )
        log(f"behaviour: {reason}")
        return {"score": 0.0, "reasoning": reason}

    with tempfile.TemporaryDirectory(prefix="titlecase-grade-") as temp_dir:
        binary = Path(temp_dir) / "titlecase"
        code, _stdout, stderr, timed_out = run_command(
            ["go", "build", "-o", str(binary), "."],
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

        # Unprivileged, bare environment, outside the workspace: the program
        # cannot read /tests or start Python (see support.py, tests/Dockerfile).
        code, stdout, stderr, timed_out = run_submission(
            binary, program_input, RUN_TIMEOUT_SEC
        )

    actual = records(stdout)
    matches = sum(
        1
        for index in range(EXAM_RECORD_COUNT)
        if index < len(actual) and actual[index] == expected[index]
    )
    score = _fraction(matches)
    contract_ok = code == 0 and not timed_out and len(actual) == EXAM_RECORD_COUNT
    if score == 1.0 and not contract_ok:
        score = _fraction(EXAM_RECORD_COUNT - 1)

    reason = (
        f"matches={matches}/{EXAM_RECORD_COUNT} "
        f"actual_records={len(actual)} exit={code} timed_out={timed_out}"
    )
    if stderr:
        diagnostic = stderr.decode("utf-8", errors="replace").strip()
        if diagnostic:
            reason = f"{reason}; stderr={diagnostic[:500]}"
    log(f"behaviour: {reason}")
    return {"score": score, "reasoning": reason}
