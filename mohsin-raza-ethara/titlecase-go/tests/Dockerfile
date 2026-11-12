FROM golang:1.23

# uvx is used at runtime to fetch Reward Kit (requires network_mode = "public"
# in task.toml so the verifier container can reach PyPI).
COPY --from=ghcr.io/astral-sh/uv:0.9.7 /uv /uvx /bin/

WORKDIR /app

# This is a dedicated verifier image: Harbor does not upload tests/ at
# runtime when tests/Dockerfile exists, so bundle the tests and hidden
# fixtures here.
COPY . /tests/
