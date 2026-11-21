FROM golang:1.23.4 AS go

FROM python:3.12-slim-bookworm

COPY --from=go /usr/local/go /usr/local/go
ENV PATH="/usr/local/go/bin:${PATH}"
RUN python -m venv /opt/rewardkit \
    && /opt/rewardkit/bin/pip install --no-cache-dir harbor-rewardkit==0.2.4
ENV PATH="/opt/rewardkit/bin:${PATH}"

WORKDIR /workspace/repo
COPY . /tests/
