import json
import os
from pathlib import Path

from rewardkit import criterion


@criterion
def compile_packages(workspace):
    return json.loads(Path(os.environ["TITLECASE_GRADE"]).read_text())["build"]
