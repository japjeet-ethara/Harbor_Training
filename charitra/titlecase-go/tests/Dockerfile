# The verifier starts clean: it does not contain the original Python repository.
FROM golang:1.23@sha256:60deed95d3888cc5e4d9ff8a10c54e5edc008c6ae3fba6187be6fb592e19e8c0 AS go_toolchain
FROM python:3.12-slim-bookworm@sha256:935c3c5b12357a7e10caa9c1e6ca5692344d97cf229832ef584be2cec9fc03df

COPY --from=go_toolchain /usr/local/go /usr/local/go
ENV PATH="/usr/local/go/bin:/usr/local/bin:/usr/bin:/bin" \
    LITELLM_LOCAL_MODEL_COST_MAP=True \
    PYTHONDONTWRITEBYTECODE=1
RUN python -m pip install --no-cache-dir 'harbor-rewardkit==0.2.4'
COPY . /tests/
RUN mkdir -p /workspace/repo /logs/verifier /run/titlecase-grader \
    && touch /tests/.container-verifier \
    && chmod 700 /tests /logs/verifier /run/titlecase-grader \
    && chmod +x /tests/test.sh
WORKDIR /workspace/repo
# Root is deliberate: RewardKit Worker drops to a fresh unprivileged UID for
# every candidate build/run, while the trusted scorer retains hidden answers.
USER root
