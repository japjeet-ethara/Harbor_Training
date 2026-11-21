#!/bin/bash
# Grade /workspace/repo. Always exit 0 after writing /logs/verifier/reward.json.
#
# Runs as root in the separate verifier container (task.toml [verifier]
# environment_mode = "separate"). Three checks, in order:
#
#   checks/no_python.sh  gate  - any .py file left in the submission scores 0
#   checks/build.sh      gate  - `go build ./...` must succeed
#   checks/behaviour.sh  score - byte-exact output on 100,000 hidden titles
#
# The two gates pay nothing on their own: a submission that passes both and
# answers nothing still scores 0.0. Only behaviour.sh produces reward.

set -u

mkdir -p /logs/verifier

TESTS=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO=/workspace/repo
export TESTS REPO

write_reward() {
  printf '{"reward": %s}\n' "$1" > /logs/verifier/reward.json
}

# ---------------------------------------------------------------------------
# Lock the exam away before anything from the submission is executed.
#
# Cheat 1 against the attacked version of this task walked /tests, /workspace
# and / looking for *_expected.txt next to an inputs file, printed the stored
# answers and scored 1.0. It worked because tests/test.sh ran the submitted
# binary as root in the same container as the answer files.
#
# Now: /tests is root-only, the submission tree is root-only, and the graded
# binary runs as uid 65534 from /var/grader where the only thing it can read or
# execute is the binary itself. stdin is opened by root before privileges are
# dropped, so the program never needs read access to the inputs either.
# ---------------------------------------------------------------------------
chown -R 0:0 "$TESTS" 2>/dev/null
chmod -R go-rwx "$TESTS" 2>/dev/null

if [[ ! -d "$REPO" ]]; then
  write_reward 0.0
  exit 0
fi

if ! bash "$TESTS/checks/no_python.sh"; then
  write_reward 0.0
  exit 0
fi

if ! bash "$TESTS/checks/build.sh"; then
  write_reward 0.0
  exit 0
fi

score=$(bash "$TESTS/checks/behaviour.sh")
case "$score" in
  ''|*[!0-9.]*) score=0.0 ;;
esac

write_reward "$score"
exit 0