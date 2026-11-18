FROM python:3.12.8-slim@sha256:2199a62885a12290dc9c5be3ca0681d367576ab7bf037da120e564723292a2f0 AS python
FROM golang:1.23@sha256:60deed95d3888cc5e4d9ff8a10c54e5edc008c6ae3fba6187be6fb592e19e8c0
COPY --from=python /usr/local /usr/local
RUN useradd -m -u 1000 candidate && mkdir -p /workspace/repo /logs/artifacts && chown -R candidate:candidate /workspace /logs/artifacts
COPY --chown=candidate:candidate repo/ /workspace/repo/
ENV PYTHONDONTWRITEBYTECODE=1 GOTOOLCHAIN=local
WORKDIR /workspace/repo
USER candidate
