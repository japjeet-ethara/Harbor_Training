#!/bin/bash
# Only root (the grader) may read the exam. The port under test runs as nobody.
chmod -R go-rwx /tests
rewardkit /tests --workspace /workspace/repo --output /logs/verifier/reward.json
