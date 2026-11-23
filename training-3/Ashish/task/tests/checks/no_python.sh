#!/bin/bash
# Check 1 (gate): no Python file may remain anywhere under the submission.
#
# This is a gate, not a scored component. Cheat 3 against the attacked task and
# an empty submission both passed the old build/no_python checks; the point of
# keeping them as gates is that passing them is worth exactly nothing.
#
# Symlinked directories are not followed, so a link to /usr cannot be used to
# make the scan time out or to hide a .py file outside the tree.
set -u
REPO=${REPO:-/workspace/repo}

if [[ ! -d "$REPO" ]]; then
  exit 1
fi

if find "$REPO" -xdev -type f -name '*.py' -print -quit | grep -q .; then
  echo "no_python: a .py file is still present" >&2
  exit 1
fi

exit 0