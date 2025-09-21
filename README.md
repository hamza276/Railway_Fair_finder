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
---
title: PakRail AI — Pakistan Railway Booking Assistant
emoji: 🚆
colorFrom: indigo
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
license: mit
---

# PakRail AI — Pakistan Railway Booking Assistant

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009485?logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61dafb?logo=react&logoColor=white)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-5-646cff?logo=vite&logoColor=white)](https://vitejs.dev/)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ed?logo=docker&logoColor=white)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

PakRail AI is a chat-based assistant to help find Pakistan Railway trains, fares, and timing windows. Users can talk in Roman Urdu or English. The assistant works fully offline via local parsing and can optionally leverage an LLM through OpenRouter for better extraction.

Frontend (Vite React) is served together with a FastAPI backend. A single Docker image serves the SPA at `/` and the API under `/api`.

---

## Table of Contents
- Features
- Architecture
- Tech Stack
- Project Structure
- Getting Started
  - Prerequisites
  - Local Development (Backend + Frontend)
  - Docker (Full Stack)
  - CLI Mode
- Environment Variables
- API Reference
- Usage Examples (Roman Urdu)
- Troubleshooting
- Security Notes
- Roadmap
- Contributing
- License
- Acknowledgements

---

## Features
- Conversational booking helper; polite Roman-Urdu tone supported.
- Guided state machine: from → to → date → budget → time → confirm.
- Offline-first parsing; optional LLM via OpenRouter (LangChain OpenAI-compatible).
- Scraper scaffolding with Selenium/requests and realistic sample data.
- Web UI (chat), REST API, and CLI experience.
- Single Docker image (serves SPA + API together).

## Architecture
- Frontend (Vite React) calls FastAPI endpoints under `/api`.
- API keeps an in-memory session map (`sessionId` → agent instance).
- Agent (FSM) extracts structured fields locally; tries LLM up to 2 times if allowed; falls back automatically on errors.
- When information is complete, scraper returns realistic train options that are formatted as list/table/json.

High-level flow:

```
UI → POST /api/chat → TrainBookingAI (local parse + optional LLM)
   → PakRailScraper → formatted reply
```

## Tech Stack
- Backend: FastAPI, Uvicorn
- Frontend: React 18 + Vite
- Scraper: Selenium, BeautifulSoup, Requests
- Agent: Python, LangChain (OpenRouter optional)
- Tooling: Rich, Colorama, dotenv
- Container: Docker, docker-compose

## Project Structure
```
Railway_Fair_finder/
├─ app_entry.py               # ASGI wrapper that mounts API + static SPA
├─ server.py                  # FastAPI routes (/api/health, /api/chat, /api/reset)
├─ main.py                    # CLI entry (terminal app)
├─ config/
│  └─ settings.py            # dotenv config (API keys, timeouts, model)
├─ modules/
│  ├─ ai_agent.py            # FSM + parsing + optional LLM calls
│  ├─ scraper.py             # Selenium/requests scaffolding + sample data
│  └─ utils.py               # Logger, DisplayManager, DataManager
├─ frontend/                 # Vite React chat UI
├─ data/                     # Saved train data (JSON)
├─ Dockerfile                # Builds frontend, runs FastAPI, serves SPA
├─ docker-compose.yml        # Dev compose (exposes 7860)
├─ requirements.txt          # Backend dependencies
└─ README.md                 # This file
```

> Note: A mirrored folder `Railway_Fair_finder/Railway_Fair_finder` may exist in some setups. Use the root-level paths above as your primary working set.

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- Chrome + Chromedriver (only if you plan to run the scraper locally; Docker avoids this)

### Local Development

Backend (dev):
```bash
pip install -r Railway_Fair_finder/requirements.txt
uvicorn Railway_Fair_finder.server:app --reload
# Health: http://127.0.0.1:8000/api/health
```

Frontend (dev):
```bash
cd Railway_Fair_finder/frontend
npm i
npm run dev
# If API is on a different origin, set VITE_API_BASE accordingly
```

### Docker (Full Stack)
```bash
cd Railway_Fair_finder
docker compose up --build
# Visit http://localhost:7860
```

The Docker image builds the React app, copies the production build into `/app/static`, and serves it from the same origin as the API (`/api`).

### CLI Mode (Terminal)
```bash
python Railway_Fair_finder/main.py
```

## Environment Variables

Backend (`Railway_Fair_finder/.env`)
- `OPENROUTER_API_KEY` — Optional. Enables LLM assist via OpenRouter; leave empty for offline mode.
- `PORT` — Optional. Defaults to `7860` in Docker.

Frontend (`Railway_Fair_finder/frontend/.env`)
- `VITE_API_BASE` — For local dev, e.g. `http://127.0.0.1:8000`. In Docker/prod, the app calls relative paths; you can omit this.

Notes
- If `OPENROUTER_API_KEY` is missing or rate-limited, the agent switches to offline parsing automatically.
- Never commit real secrets. Rotate any leaked keys immediately.

## API Reference

Base URL: dev `http://127.0.0.1:8000`, docker `http://localhost:7860`

- `GET /api/health`
  - `200 OK` → `{ "status": "ok" }`

- `POST /api/chat`
  - Request JSON: `{ "message": "string", "sessionId": "optional-uuid" }`
  - Response JSON: `{ "reply": "string", "sessionId": "uuid" }`
  - Provide `sessionId` to continue a conversation; omit to start a new one.

- `POST /api/reset`
  - Request JSON: `{ "sessionId": "optional-uuid" }`
  - Response JSON: `{ "ok": true }`

Examples
```bash
curl http://127.0.0.1:8000/api/health

curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"message":"karachi se lahore kal raat"}' \
  http://127.0.0.1:8000/api/chat

curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"sessionId":"<your-sid>"}' \
  http://127.0.0.1:8000/api/reset
```

## Usage Examples (Roman Urdu)
- "mujhe karachi se lahore jana hai"
- "kal raat business class"
- "budget economy, format table"
- "reset" — naya search start karne ke liye

## Troubleshooting
- Chrome/Chromedriver: Prefer Docker to avoid local browser setup. For local runs, ensure Chrome + matching Chromedriver is installed and on PATH. See `modules/scraper.py` for auto-detection and fallbacks.
- CORS in dev: API is permissive by default; confirm `VITE_API_BASE` in the frontend `.env`.
- Garbled CLI glyphs: Some decorative characters in console strings may look odd in certain terminals; cosmetic only.
- LLM not responding: Remove the API key or leave it empty to stay in offline mode; local parsing covers common phrases.

## Security Notes
- Do not commit `.env` with real secrets. If a secret was committed, consider it leaked and rotate it.
- The repo `.gitignore` excludes `.env`, but already-tracked files will remain; remove them from history if needed.

## Roadmap
- Live data integration with stable selectors and anti-bot mitigation.
- Better NER for station names and dates.
- Persistent session store (beyond in-memory) for multi-instance deployments.
- Multi-language UI (Urdu script + English).

## Contributing
Contributions are welcome! Please:
- Keep changes minimal and focused.
- Maintain user-facing Roman-Urdu tone in `ai_agent.py`.
- Update README and frontend calls if you change API endpoints or payloads.

## License
MIT — see front matter. Add a `LICENSE` file if you plan to distribute.

## Acknowledgements
- FastAPI, Uvicorn, React, Vite
- Selenium, BeautifulSoup, Requests
- LangChain, OpenRouter (optional)
- Rich, Colorama
