# Agent room: Go on Alpine (no Python at all), bash for Harbor, non-root user.
# The reference Go port is NOT in this image; it lives only in solution/ (oracle runs only).
FROM golang:1.23-alpine@sha256:383395b794dffa5b53012a212365d40c8e37109a626ca30d6151c8348d380b5f
RUN apk add --no-cache bash \
 && adduser -D -u 1000 player
ENV CGO_ENABLED=0 \
    GOTOOLCHAIN=local
COPY --chown=player:player python-titlecase/ /workspace/repo/
RUN rm -rf /workspace/repo/.git /workspace/repo/.github
USER player
WORKDIR /workspace/repo
