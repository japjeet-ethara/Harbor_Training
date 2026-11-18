FROM python:3.12-slim-bookworm

COPY --from=golang:1.23 /usr/local/go /usr/local/go

ENV PATH="/usr/local/go/bin:${PATH}" \
    PIP_BREAK_SYSTEM_PACKAGES=1

RUN pip install --no-cache-dir "harbor-rewardkit==0.2.4"

WORKDIR /workspace/repo

COPY . /tests/
