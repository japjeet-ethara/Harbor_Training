from pathlib import Path
from rewardkit import criterion
from grader import evaluate


@criterion
def exact_hidden_titlecase_records(workspace: Path) -> float:
    """Exact UTF-8 records; missing/extra records or failed execution receive zero."""
    return evaluate(workspace)["behaviour"]
