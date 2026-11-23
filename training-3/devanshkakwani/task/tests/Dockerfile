FROM golang:1.23-bookworm AS go

FROM python:3.12-slim-bookworm

COPY --from=go /usr/local/go /usr/local/go

ENV GOROOT=/usr/local/go
ENV PATH="/usr/local/go/bin:${PATH}"

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential fuse-overlayfs \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir 'harbor-rewardkit>=0.2.4'

# The binary under test runs as `nobody` (tests/behaviour.py). Rewardkit runs as
# root, which ignores these mode bits, so only the submission loses access to
# every interpreter and toolchain in this image (Python, Perl, awk, shells, Go).
# o-rwx, not just o-x: ld.so cannot load a file it cannot read either.
RUN chmod o-rwx \
        /usr/local/bin/python3.12 \
        /usr/local/lib/libpython3.12.so.1.0 \
        /usr/local/lib/python3.12 \
        /usr/bin/perl /usr/bin/perl5.36.0 \
        /usr/bin/mawk \
        /usr/bin/bash /usr/bin/dash \
        /usr/local/go \
    && python -I -c "import rewardkit, re, json, ctypes; print('rewardkit imports as root')"

# Build fails unless `nobody` is locked out of every interpreter above.
COPY lockdown_check.py /tmp/lockdown_check.py
RUN python -I /tmp/lockdown_check.py && rm /tmp/lockdown_check.py

WORKDIR /app

COPY . /tests/
