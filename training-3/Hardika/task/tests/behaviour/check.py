import json
import os
from pathlib import Path

from rewardkit import criterion


@criterion
def check_hidden_agreement(workspace):
    return json.loads(Path(os.environ["TITLECASE_GRADE"]).read_text())["behaviour"]
