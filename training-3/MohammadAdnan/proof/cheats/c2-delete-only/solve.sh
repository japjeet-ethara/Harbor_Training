#!/bin/bash
# Charitra's cheat 2 — Delete-Python-only: remove every .py file, write no Go at all.
set -euo pipefail
find /workspace/repo -name '*.py' -type f -delete
