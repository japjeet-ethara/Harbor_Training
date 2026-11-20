FROM python:3.12-slim-bookworm

COPY --from=golang:1.23 /usr/local/go /usr/local/go
ENV PATH="/usr/local/go/bin:${PATH}"
ENV CGO_ENABLED=0

RUN pip install --no-cache-dir "harbor-rewardkit==0.2.4"

COPY . /tests/
RUN chmod 755 /tests/test.sh

WORKDIR /workspace/repo
