# Pinned toolchain image.
#
# Harbor's build context is this environment/ folder, so the pristine snapshot
# of ppannuto/python-titlecase 2.4.1 (commit
# 42f43e2de55bf003b286c6f8e8d8b2d26676a167, MIT) is vendored next to this file
# in environment/python-titlecase/. Before hardening this Dockerfile said
# "the build context is ../python-titlecase" and copied "." , so the agent got
# a /workspace/repo containing nothing but this Dockerfile and the task was
# unsolvable as written.
FROM golang:1.23

COPY python-titlecase/ /workspace/repo/
RUN rm -rf /workspace/repo/.git

# Cheat 2 against the attacked version of this task kept the original Python
# source under a non-.py name and ran it with the python3 that golang:1.23
# inherits from Debian, scoring 1.0 with no Go port at all. task.toml sets
# [verifier] environment_mode = "separate", and Harbor builds that verifier
# container from a fresh copy of this same image, so removing every interpreter
# here removes it from the graded container too.
RUN rm -rf /usr/bin/python3* /usr/bin/python /usr/lib/python3 /usr/lib/python3.* \
           /usr/local/lib/python3* /usr/share/python3* /etc/python3* \
           /usr/bin/perl /usr/bin/perl5* /usr/share/perl /usr/share/perl5 \
           /usr/lib/*/perl /usr/lib/*/perl5 \
           /usr/bin/ruby* /usr/bin/node /usr/bin/nodejs /usr/bin/php* \
 && for exe in python python3 perl ruby node nodejs php; do \
        if command -v "$exe" >/dev/null 2>&1; then \
            echo "interpreter still present: $exe" >&2; exit 1; \
        fi; \
    done \
 && echo "no scripting interpreter left in the image"

# tests/checks/behaviour.sh installs the one binary it is willing to run here.
# Nothing else in this directory is readable by the unprivileged grading user.
RUN install -d -m 0755 /var/grader

WORKDIR /workspace/repo