FROM golang:1.23

COPY --exclude=.git --exclude=tests --exclude=solution --exclude=cheat --exclude=environment --exclude=screenshots --exclude=task.toml --exclude=reward.toml --exclude=test.sh --exclude=test_outputs.py --exclude=gen.py --exclude=Dockerfile . /workspace/repo

WORKDIR /workspace/repo
