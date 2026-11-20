#!/bin/bash
# Verifier entry point. Runs in the verifier container (tests/Dockerfile) after the agent
# has finished; /workspace/repo is the agent's final repository, carried over by Harbor.
# grade.py always writes /logs/verifier/reward.json, even if a check crashes.
mkdir -p /logs/verifier
exec python3 /tests/grade.py /workspace/repo /tests/data/graded /logs/verifier/reward.json
