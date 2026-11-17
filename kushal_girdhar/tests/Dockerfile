FROM golang:1.23@sha256:60deed95d3888cc5e4d9ff8a10c54e5edc008c6ae3fba6187be6fb592e19e8c0 AS go
FROM python:3.12.14-slim-bookworm@sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e
COPY --from=go /usr/local/go /usr/local/go
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 LITELLM_LOCAL_MODEL_COST_MAP=True LITELLM_TELEMETRY=False DO_NOT_TRACK=1
COPY requirements.lock /tmp/requirements.lock
RUN python -m pip --disable-pip-version-check install --no-cache-dir --only-binary=:all: --require-hashes -r /tmp/requirements.lock \
    && rm /tmp/requirements.lock
COPY --chmod=0700 test.sh /tests/test.sh
COPY evaluator.py isolate.py reward.toml /tests/
COPY build/ /tests/build/
COPY no_python/ /tests/no_python/
COPY behaviour/ /tests/behaviour/
COPY data/hidden_inputs.txt data/hidden_expected.txt /tests/data/
RUN chmod 0700 /tests /tests/data && chmod 0600 /tests/data/*.txt
WORKDIR /workspace
