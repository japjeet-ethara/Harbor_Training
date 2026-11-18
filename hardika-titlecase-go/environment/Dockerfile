FROM golang:1.23.12-bookworm@sha256:167053a2bb901972bf2c1611f8f52c44d5fe7e762e5cab213708d82c421614db
COPY --from=python:3.12.14-slim-bookworm@sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e /usr/local/ /usr/local/
COPY requirements.lock /tmp/reference-requirements.lock
RUN /usr/local/bin/python -m pip install --no-cache-dir --only-binary=:all: --require-hashes -r /tmp/reference-requirements.lock \
    && /usr/local/bin/python -c 'import regex, ssl, sys, unicodedata; assert sys.version_info[:3] == (3,12,14); assert unicodedata.unidata_version == "15.0.0"; assert regex.DEFAULT_VERSION == regex.VERSION0' \
    && rm /tmp/reference-requirements.lock
ENV PYTHONDONTWRITEBYTECODE=1 CGO_ENABLED=0 GOENV=off GOTOOLCHAIN=local GOPROXY=off GOSUMDB=off
RUN useradd --create-home --uid 10001 agent && install -d -o agent -g agent /workspace/repo
WORKDIR /workspace/repo
COPY --chown=agent:agent upstream/ /workspace/repo/
