FROM python:3.12-slim

COPY --from=golang:1.23 /usr/local/go /usr/local/go
ENV PATH="/usr/local/go/bin:${PATH}"
ENV GOTOOLCHAIN=local

# Reward Kit's worker executes this interpreter as an unprivileged user.
# A uvx install under /root is not executable by that user, so the verifier
# exits before writing /logs/verifier/reward.json.
RUN pip install --no-cache-dir 'harbor-rewardkit>=0.2.4'

WORKDIR /workspace/repo
COPY . /tests/
