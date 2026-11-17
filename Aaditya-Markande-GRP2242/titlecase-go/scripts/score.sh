#!/bin/bash
cd /workspaces/titlecase-go
rm -rf /tmp/vlogs && mkdir -p /tmp/vlogs
docker run --rm -v "$PWD/$1:/solve.sh:ro" -v "$PWD/tests:/tests:ro" -v /tmp/vlogs:/logs/verifier \
  titlecase-go-env bash -c "bash /solve.sh; bash /tests/test.sh"