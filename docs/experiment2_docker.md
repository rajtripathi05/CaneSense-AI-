# Experiment 2 — Docker and Docker Hub

Student: Raj Tripathi · Roll 16014223062 · Batch B1 AIDS · Prof. Sagar Korde · Use case KJS-AGR-01

## Verification status

| Step | Status |
|---|---|
| `Dockerfile` and `.dockerignore` written | Done (content validated by `tests/test_deployment_files.py`) |
| Image built | **Not executed** — Docker is not installed on this machine |
| Container run and accessibility check | **Not executed** |
| Docker Hub tag/push | **Not executed** (needs a Docker Hub account and `docker login`) |

No screenshots, logs or Docker Hub URLs are included because none were produced. Record real evidence in `evidence/exp2_docker/` after running the steps below, then set `status.json` to `"executed"`.

## Objective

Package CaneSense AI as a portable container image, run it, verify it responds on port 8501, and publish it to Docker Hub.

## Design (`Dockerfile`)

- Base `python:3.11-slim`; dependencies from `requirements.txt` (cached layer).
- Copies `app.py`, `canesense/`, `views/`, `assets/`, `scripts/`, `experiments/`, `evidence/`, `data/`, `docs/`, `.streamlit/` — the same asset structure as local development.
- Trains the model during the build (`python scripts/train_model.py`) so the pickle matches the image's scikit-learn.
- Runs as non-root user (UID 10001). `HEALTHCHECK` calls `/_stcore/health`. Exposes 8501.
- `.dockerignore` excludes scratch files, tests, outputs, old model pickles and git metadata.

## Commands

```powershell
# 1. Build
docker build -t canesense-ai:1.0 .

# 2. Run
docker run -d --name canesense -p 8501:8501 canesense-ai:1.0

# 3. Verify
docker ps                                           # STATUS should become "healthy"
curl.exe http://localhost:8501/_stcore/health       # expect: ok
start http://localhost:8501                          # app should load with the hero image

# 4. Inspect
docker logs canesense
docker exec canesense ls /app/assets/images          # assets present inside the image

# 5. Docker Hub (replace <user> with your Docker Hub username)
docker login
docker tag canesense-ai:1.0 <user>/canesense-ai:1.0
docker tag canesense-ai:1.0 <user>/canesense-ai:latest
docker push <user>/canesense-ai:1.0
docker push <user>/canesense-ai:latest

# 6. Clean up
docker rm -f canesense
```

## Evidence to capture

`docker build` output tail, `docker ps` showing *healthy*, the health-check response, a browser screenshot of the container-served app, and the Docker Hub repository page.

## Expected conclusion (to be written only after execution)

State the final image size (`docker images canesense-ai:1.0`), build time and any problems encountered.
