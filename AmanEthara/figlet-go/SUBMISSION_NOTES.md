1. Smushing challenge: The interaction between right-to-left print direction (`-D right-to-left`) and justification, as well as universal smushing and hardblank handling across disparate font dimensions, required strict adherence to pyfiglet's FigletBuilder precedence rules.

2. Docker challenge: Alpine Linux excludes `bash` by default (which Harbor requires to launch trial commands), and ensuring the multi-stage build completely removed Python, finished the Makefile font setup into `/workspace/repo/pyfiglet/fonts`, and ran strictly as non-root user `player` (UID 1000).
