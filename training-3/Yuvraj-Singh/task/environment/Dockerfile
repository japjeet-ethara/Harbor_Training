FROM golang:1.23

# The agent ports this tree. .git is not part of the build context.
COPY python-titlecase/ /workspace/repo/

# Remove Python venv and any python-named files from the source tree, and remove system python.
RUN rm -rf /workspace/repo/.venv && \
    find /workspace/repo -type f -name 'python*' -delete 2>/dev/null; \
    find /workspace/repo -type f -name 'py_*' -delete 2>/dev/null; \
    rm -f /usr/bin/python* /usr/local/bin/python* /bin/python*; \
    true

WORKDIR /workspace/repo
