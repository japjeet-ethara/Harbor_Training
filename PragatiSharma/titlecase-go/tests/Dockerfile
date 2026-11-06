FROM python:3.12-slim-bookworm

COPY --from=golang:1.23 /usr/local/go /usr/local/go

ENV PATH="/usr/local/go/bin:${PATH}" \
    GOTOOLCHAIN=local \
    CGO_ENABLED=0 \
    GOCACHE=/tmp/go-cache \
    GOMODCACHE=/tmp/go-mod \
    GOPATH=/tmp/gopath

RUN pip install --no-cache-dir harbor-rewardkit==0.2.4 \
    && python -c "import importlib.metadata as m; assert m.version('harbor-rewardkit') == '0.2.4'"

WORKDIR /tests

COPY . /tests/
