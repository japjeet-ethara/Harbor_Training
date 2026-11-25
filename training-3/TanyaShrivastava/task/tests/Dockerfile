# The examiner's room: separate from the agent's container.
# It gets the agent's /workspace/repo re-materialised as a task artifact.
FROM python:3.12-bookworm

COPY --from=golang:1.23.9-bookworm /usr/local/go /usr/local/go

RUN pip3 install --no-cache-dir "harbor-rewardkit==0.2.4" pytest

ENV PATH="/usr/local/go/bin:${PATH}" \
    GOTOOLCHAIN=local \
    GOFLAGS=-buildvcs=false \
    GOPROXY=off

WORKDIR /app
COPY . /tests/