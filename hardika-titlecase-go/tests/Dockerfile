FROM golang:1.23.12-bookworm@sha256:167053a2bb901972bf2c1611f8f52c44d5fe7e762e5cab213708d82c421614db
COPY --from=python:3.12.14-slim-bookworm@sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e /usr/local/ /usr/local/
ENV LITELLM_LOCAL_MODEL_COST_MAP=True
COPY requirements.lock /tmp/verifier-requirements.lock
RUN /usr/local/bin/python -m pip install --no-cache-dir --require-hashes --only-binary=:all: -r /tmp/verifier-requirements.lock \
    && /usr/local/bin/rewardkit --help >/dev/null \
    && rm /tmp/verifier-requirements.lock \
    && mkdir -p /workspace/repo /tests/data \
    && chmod 700 /tests
COPY grade.py reward.toml test.sh /tests/
COPY build/check.py /tests/build/check.py
COPY no_python/check.py /tests/no_python/check.py
COPY behaviour/check.py /tests/behaviour/check.py
COPY data/hidden_inputs.txt data/hidden_expected.txt /tests/data/
WORKDIR /
