FROM golang:1.23 AS build

WORKDIR /src
COPY server.go .
RUN CGO_ENABLED=0 GOOS=linux go build -trimpath -ldflags="-s -w" -o /runner server.go

FROM scratch
COPY --from=build /runner /runner
WORKDIR /workspace/repo
ENTRYPOINT ["/runner"]
