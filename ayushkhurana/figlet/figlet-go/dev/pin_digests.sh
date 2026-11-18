#!/bin/bash
# Pin the two base images of environment/Dockerfile by digest (rule D5).
# Run it once on a machine with Docker, from the task folder:   bash dev/pin_digests.sh
# It pulls each image, reads the digest that `docker pull` prints, and rewrites the FROM lines
# to  image:tag@sha256:...   (running it again just refreshes the digests).
set -euo pipefail
cd "$(dirname "$0")/.."
file=environment/Dockerfile

pin() {  # pin <image:tag>
  local ref=$1 digest
  digest=$(docker pull "$ref" | sed -n 's/^Digest: \(sha256:[0-9a-f]\{64\}\)$/\1/p')
  [ -n "$digest" ] || { echo "could not read the digest of $ref" >&2; exit 1; }
  echo "$ref -> $digest" >&2
  sed -i -E "s#^FROM ${ref}(@sha256:[0-9a-f]+)?( |\$)#FROM ${ref}@${digest}\2#" "$file"
}

pin alpine:3.20
pin golang:1.23-alpine
grep -n '^FROM' "$file"
