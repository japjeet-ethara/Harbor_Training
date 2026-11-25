import json
import os
from pathlib import Path

from rewardkit import criterion


@criterion
def check_python_removal(workspace):
    return json.loads(Path(os.environ["TITLECASE_GRADE"]).read_text())["no_python"]
