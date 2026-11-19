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

# The grader runs as root. The submitted program runs as UID 40000
# (grade/support.py). Make /tests (including the graded answers,
# data/answers.txt) and the Python interpreter root-only, then prove UID 40000
# can use neither. The image build fails if not.
RUN chmod -R go-rwx /tests \
    && chmod 0700 /usr/local/bin/python3.12 \
                  /usr/local/lib/libpython3.12.so.1.0 \
                  /usr/local/lib/libpython3.so \
                  /usr/local/lib/python3.12 \
    && setpriv --reuid=40000 --regid=40000 --clear-groups -- true \
    && for p in python3 python /usr/bin/python3 /usr/local/bin/python3 /usr/bin/python /usr/local/bin/python3.12; do \
         if setpriv --reuid=40000 --regid=40000 --clear-groups -- "$p" -c pass 2>/dev/null; then \
           echo "UID 40000 can still run $p" >&2; exit 1; \
         fi; \
       done \
    && test -s /tests/data/answers.txt \
    && if setpriv --reuid=40000 --regid=40000 --clear-groups -- cat /tests/data/answers.txt >/dev/null 2>&1; then \
         echo "UID 40000 can still read the graded answers" >&2; exit 1; \
       fi \
    && python -c "import rewardkit"
