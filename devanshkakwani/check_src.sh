#!/bin/bash
docker run --rm python:3.12-slim bash -c '
pip install -q "harbor-rewardkit==0.2.*"
python3 -c "
with open(\"/usr/local/lib/python3.12/site-packages/rewardkit/runner.py\") as f:
    lines = f.readlines()
for i, line in enumerate(lines[120:260], 121):
    print(f\"{i}: {line}\", end=\"\")
"
'
