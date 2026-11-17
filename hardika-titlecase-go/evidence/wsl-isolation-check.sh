#!/usr/bin/env bash
set -euxo pipefail
docker run --rm --network none --user 10001:10001 titlecase-go-agent:section18 bash -ec '
    test "$PWD" = /workspace/repo
    test -w .
    test -f titlecase/__init__.py
    test ! -e /tests
    test "$(ls /sys/class/net)" = lo
    printf "%s\n" "Starter workspace is writable as the agent, with only loopback networking and no tests directory."
'
docker run --rm --network none --user 65534:65534 titlecase-go-verifier:section18 bash -ec '
    test ! -r /tests/data/hidden_expected.txt
    test "$(ls /sys/class/net)" = lo
    printf "%s\n" "The candidate UID cannot read expected answers and has only loopback networking."
'
