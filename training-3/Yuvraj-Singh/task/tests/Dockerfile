FROM golang:1.23

COPY --from=ghcr.io/astral-sh/uv:0.9.7 /uv /uvx /bin/

# Reward Kit is installed in the verifier image so grading does not depend on
# a package download at verify time. The agent image does not include it.
RUN uv python install 3.12 \
    && uv tool install --python 3.12 'harbor-rewardkit==0.2.*'

ENV PATH="/root/.local/bin:${PATH}"

COPY . /tests/
WORKDIR /workspace/repo
