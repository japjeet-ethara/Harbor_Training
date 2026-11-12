FROM golang:1.23

# python-titlecase/ is copied into this directory (environment/) so it falls
# inside the Docker build context.  Harbor uses environment/ as the build
# context, so we cannot reference ../python-titlecase directly.
COPY python-titlecase/ /workspace/repo/

WORKDIR /workspace/repo
