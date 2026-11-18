import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
summary = {}
for name, target in [('oracle', 1.0), ('nop', 0.0), ('replay-cheat', 1/6)]:
    rewards = list((root / 'jobs' / name).glob('*/verifier/reward.json'))
    assert len(rewards) == 1, (name, rewards)
    reward = json.loads(rewards[0].read_text())
    assert set(reward) == {'reward'}, reward
    measured = reward['reward']
    assert abs(measured-round(target, 4)) < 1e-12, (name, measured)
    checks = json.loads((rewards[0].parent / 'checks.json').read_text())
    summary[name] = dict(reward=measured, checks=checks['checks'], reward_file=rewards[0].relative_to(root).as_posix())
assert summary['replay-cheat']['reward'] < .2
(root / 'summary.json').write_text(json.dumps(summary, indent=2)+'\n', encoding='utf-8')
print(json.dumps(summary, indent=2))
