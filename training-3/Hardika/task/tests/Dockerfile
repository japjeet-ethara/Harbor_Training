FROM golang:1.23.12-bookworm@sha256:167053a2bb901972bf2c1611f8f52c44d5fe7e762e5cab213708d82c421614db
COPY --from=python:3.12.14-slim-bookworm@sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e /usr/local/ /usr/local/
ENV LITELLM_LOCAL_MODEL_COST_MAP=True
COPY requirements.lock /tmp/verifier-requirements.lock
RUN /usr/local/bin/python -m pip install --no-cache-dir --require-hashes --only-binary=:all: -r /tmp/verifier-requirements.lock \
    && /usr/local/bin/rewardkit --help >/dev/null \
    && rm /tmp/verifier-requirements.lock \
    && mkdir -p /workspace/repo /tests/data \
    && chmod 700 /tests
# The candidate program runs as uid 65534 (see grade.py) and must not be able to start any
# Python interpreter; root (grade.py and rewardkit) keeps full access. The last loop makes
# the image build fail if uid 65534 can still run one.
RUN for f in /usr/local/bin/python3* /usr/bin/python3*; do \
        if [ -e "$f" ]; then chmod o-rwx "$(readlink -f "$f")"; fi; \
    done \
    && for d in /usr/local/lib/python3* /usr/lib/python3*; do \
        if [ -d "$d" ]; then chmod o-rwx "$d"; fi; \
    done \
    && /usr/local/bin/python -c 'import rewardkit' \
    && for f in /usr/local/bin/python3 /usr/bin/python3; do \
        if [ -e "$f" ] && setpriv --reuid=65534 --regid=65534 --clear-groups "$f" -c pass 2>/dev/null; then \
            echo "uid 65534 can still run $f" >&2; exit 1; \
        fi; \
    done
COPY grade.py reward.toml test.sh /tests/
COPY build/check.py /tests/build/check.py
COPY no_python/check.py /tests/no_python/check.py
COPY behaviour/check.py /tests/behaviour/check.py
COPY data/inputs.txt data/answers.txt /tests/data/
WORKDIR /
