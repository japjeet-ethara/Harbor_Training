# ── Stage 1: source ──────────────────────────────────────────────────────────
# alpine/git – small image that ships git; pin by digest for reproducibility
FROM alpine/git:2.43.0 AS source

# Clone pyfiglet and check out the exact commit required
RUN git clone https://github.com/pwaller/pyfiglet /src && \
    git -C /src checkout 255827efbc09d662875dad50fa0edc1e1263bf45

# Strip everything the agent doesn't need
RUN rm -rf /src/.git \
           /src/pyfiglet/fonts-contrib \
           /src/test-fonts

# Font setup: populate pyfiglet/fonts/ from the standard set
RUN mkdir -p /src/pyfiglet/fonts && \
    cp /src/pyfiglet/fonts-standard/* /src/pyfiglet/fonts/

# ── Stage 2: agent room ───────────────────────────────────────────────────────
FROM golang:1.23-alpine

# Install bash (not present by default in golang:alpine)
RUN apk add --no-cache bash

# Non-root user "player" with uid 1000
RUN adduser -D -u 1000 player

# Copy the prepared source tree from stage 1, owned by player
COPY --from=source --chown=player:player /src /workspace/repo

# Go build settings
ENV CGO_ENABLED=0 \
    GOTOOLCHAIN=local

# Drop to the non-root user
USER player

# Working directory inside the image
WORKDIR /workspace/repo
