# Komal: Windows quick start

Use the Ubuntu/WSL and Docker Desktop setup described in the chat. Keep Docker Desktop running. Download `komal-titlecase-go.zip`, then use Ubuntu to extract it so script permissions are preserved.

If the ZIP is in the same Windows Downloads folder used earlier:

```sh
mkdir -p ~/harbor-submissions
cd ~/harbor-submissions
unzip /mnt/c/Users/KushalGirdhar/Downloads/komal-titlecase-go.zip
cd komal-titlecase-go
uv venv --python 3.12.14
source .venv/bin/activate
uv pip install -r requirements-dev.txt
python tools/validate.py .
```

Expected rewards: oracle 1.0, nop 0.0, cheat below 0.2 (expected 0.1667). New results go under `evidence/reruns/`; look for `"passed": true` in the new baselines.json. Preserve the bundled logs and record screenshots of your own run separately if required.

For GitHub, upload the extracted task into its own repository or a `Komal/` folder in the training repository, following the trainer's naming convention. Include the source, tests, data, documentation, license files, and evidence. Do not upload `.venv`, caches, or collected binary artifact folders. No GitHub account, email, or surname has been assumed for Komal. Set the correct identity before committing. Use a normal push; never force-push the shared training repository.

The included Harbor scores were obtained using the cloud profile documented in evidence/validation-profile.json. The commands above check the ordinary standalone Dockerfiles on your own machine.
