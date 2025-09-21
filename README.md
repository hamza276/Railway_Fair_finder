---
title: Fullstack FastAPI + Vite on Spaces
emoji: 🚀
colorFrom: indigo
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
license: mit
---

# Fullstack FastAPI + Vite on Hugging Face Spaces (Docker)

This Space runs a single Docker container that serves a Vite React frontend and a FastAPI backend (mounted at **/api**).

## Local (Docker)

```bash
docker build -t fullstack .
docker run -p 7860:7860 fullstack
# Visit http://localhost:7860
```

## Deploy to Hugging Face Spaces
- Ensure the YAML front-matter above includes `sdk: docker` and `app_port: 7860`.
- Push this repo to your Space; the platform will build the Dockerfile and run the app on port 7860.
