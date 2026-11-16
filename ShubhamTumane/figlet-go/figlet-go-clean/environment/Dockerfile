FROM alpine/git:2.47.2 AS source
WORKDIR /src
RUN git clone https://github.com/pwaller/pyfiglet . &&     git checkout 255827efbc09d662875dad50fa0edc1e1263bf45 &&     rm -rf .git pyfiglet/fonts-contrib test-fonts &&     mkdir -p pyfiglet/fonts &&     cp pyfiglet/fonts-standard/* pyfiglet/fonts/

FROM golang:1.23-alpine
RUN apk add --no-cache bash &&     adduser -D -u 1000 player &&     mkdir -p /workspace/repo
COPY --from=source --chown=player:player /src /workspace/repo
RUN chown -R player:player /workspace
ENV CGO_ENABLED=0 GOTOOLCHAIN=local
USER player
WORKDIR /workspace/repo
