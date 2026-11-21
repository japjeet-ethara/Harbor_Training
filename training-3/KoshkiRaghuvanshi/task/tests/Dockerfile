FROM python:3.12-bookworm

COPY --from=golang:1.23 /usr/local/go /usr/local/go
ENV PATH="/usr/local/go/bin:${PATH}"

RUN python3 -m venv --copies /opt/rewardkit \
    && /opt/rewardkit/bin/pip install --no-cache-dir 'harbor-rewardkit>=0.2.4' \
    && rm -f /usr/bin/python* /bin/python* \
    && rm -f /usr/bin/python* /bin/python* \
    && chmod -R a+rX /opt/rewardkit /usr/local

COPY . /tests/
RUN chmod -R a+rX /tests
