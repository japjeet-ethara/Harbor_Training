# Measured results and blocked checks

Measured:

- Go 1.23.12 Windows build of the complete port succeeded.
- Go 1.23.12 Linux amd64 cross-build of the Go grader succeeded.
- Go WebAssembly rendering check: visible 2000/2000; hidden 2000/2000. See wasm-comparison.json.
- Three separate invocations of the unmodified WebAssembly CLI matched frozen answers. Both secret banners rendered. See wasm-cli-spot-checks.json and the two secret text captures.
- Seeded regeneration, disjoint sets, three upstream CLI spot checks, two upstream smushing checks passed. See generation-checks.json.
- Harbor task configuration model accepted player, 3600-second agent timeout, public environment networking, and 900-second verifier timeout.

Not measured: Docker build/runtime D1-D6 checks and Harbor rewards. Expected rewards are not substituted for measured rewards.

Observed environment errors:

```text
docker info:
failed to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine
open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified.

docker desktop start:
Failed to start Docker Desktop
starting Docker Desktop: getting launcher path: cannot find registry key
"SOFTWARE\\Docker Inc.\\Docker Desktop": The system cannot find the file specified.

harbor --version:
Program 'harbor.exe' failed to run: An Application Control policy has blocked this file

Launching the compiled Windows Go port:
OSError: [WinError 4551] An Application Control policy has blocked this file

wsl --status:
Access is denied. Error code: Wsl/E_ACCESSDENIED
```

No genuine reward screenshots can exist until the three Harbor runs complete. No replacement screenshots were manufactured. Run ../validate.sh in a working Docker/Harbor environment to finish this validation step.
