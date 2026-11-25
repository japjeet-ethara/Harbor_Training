FROM golang:1.23

COPY --from=python-titlecase --exclude=.git --exclude=__pycache__ / /workspace/repo/titlecase

WORKDIR /workspace/repo
