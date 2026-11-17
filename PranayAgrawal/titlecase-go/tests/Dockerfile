FROM golang:1.23 AS go

FROM python:3.12-slim

# The verifier builds and runs the submitted Go program, so it needs the Go
# toolchain from the agent image.
COPY --from=go /usr/local/go /usr/local/go
ENV PATH=/usr/local/go/bin:$PATH \
    GOTOOLCHAIN=local \
    CGO_ENABLED=0 \
    PYTHONDONTWRITEBYTECODE=1

ENV LITELLM_LOCAL_MODEL_COST_MAP=True

RUN pip install --no-cache-dir 'harbor-rewardkit==0.2.4'

RUN mkdir -p /tests
COPY test.sh reward.toml /tests/
COPY build /tests/build
COPY no_python /tests/no_python
COPY behaviour /tests/behaviour
COPY data /tests/data

RUN chmod +x /tests/test.sh

WORKDIR /workspace/repo
