import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import criteria as _criteria
import rewardkit as rk

rk.no_python_check(name="no_python")
