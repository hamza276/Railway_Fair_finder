# LLM Start Here — PakRail AI (Single Guide)

This document gives any LLM or developer everything needed to understand, run, and extend this project in one place.

## Purpose
- Chat-based Pakistan Railway booking assistant with a FastAPI backend and a Vite React frontend.
- Natural (Roman Urdu + English) conversation flow that parses route, date, budget/class, and time preference, then returns formatted train options (list/table/json).
- Optional LLM assistance via OpenRouter; works fully offline with local parsing + sample data.

## Quick Start
- Backend (dev)
  - Install: `pip install -r Railway_Fair_finder/requirements.txt`
  - Run API: `uvicorn Railway_Fair_finder.server:app --reload`
  - Health: `curl http://127.0.0.1:8000/api/health`
- Frontend (dev)
  - `cd Railway_Fair_finder/frontend && npm i && npm run dev`
  - Configure `VITE_API_BASE` in `Railway_Fair_finder/frontend/.env` (e.g., `http://127.0.0.1:8000`)
- Docker (full stack)
  - `cd Railway_Fair_finder && docker compose up --build`
  - Visit: `http://localhost:7860`

## Environment Variables (Single Source)
Place these in `Railway_Fair_finder/.env` (backend) and `Railway_Fair_finder/frontend/.env` (frontend) as needed.

Backend (`Railway_Fair_finder/.env`):
- `OPENROUTER_API_KEY` — Optional. Enables LLM assist via OpenRouter (LangChain OpenAI-compatible).
- `PORT` — Optional. Default `7860` for Docker runtime.

Frontend (`Railway_Fair_finder/frontend/.env`):
- `VITE_API_BASE=http://127.0.0.1:8000` — API base during local dev.

Notes:
- If `OPENROUTER_API_KEY` is missing or rate-limited, the agent switches to offline mode automatically.
- Docker image serves the built frontend from `/` and the API under `/api`.

## API
Base URL: dev `http://127.0.0.1:8000`, docker `http://localhost:7860`

- GET `/api/health`
  - 200 → `{ "status": "ok" }`

- POST `/api/chat`
  - Request JSON: `{ "message": "string", "sessionId": "optional-uuid" }`
  - Response JSON: `{ "reply": "string", "sessionId": "uuid" }`
  - Notes: Provide `sessionId` to continue a conversation; omit for a new session.

- POST `/api/reset`
  - Request JSON: `{ "sessionId": "optional-uuid" }`
  - Response JSON: `{ "ok": true }`

Examples:
```
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

## High-Level Architecture
- Frontend (Vite React) sends chat messages to FastAPI.
- `server.py` keeps a minimal in-memory session store mapping `sessionId` → `TrainBookingAI` instance.
- `TrainBookingAI` (FSM) tries local extraction first; if not enough info, it may do up to 2 LLM JSON extraction calls via OpenRouter; falls back gracefully on errors.
- When enough details are gathered, `PakRailScraper` is called to produce results (currently realistic sample data, with Selenium/requests scaffolding and cleanup).
- Reply formatting supports list (default), table, and json.

Text Flow:
```
UI → POST /api/chat → TrainBookingAI (local parse → optional LLM) → PakRailScraper → formatted reply
```

## Files You’ll Touch Most
- Backend API: `Railway_Fair_finder/server.py`
- Agent (FSM + parsing + LLM): `Railway_Fair_finder/modules/ai_agent.py`
- Scraper (Selenium/requests, sample data): `Railway_Fair_finder/modules/scraper.py`
- Config (dotenv-based): `Railway_Fair_finder/config/settings.py`
- Frontend App: `Railway_Fair_finder/frontend/src/App.jsx`
- Docker Entrypoint (ASGI wrapper + static): `Railway_Fair_finder/app_entry.py`

## Agent: State Machine & Behavior
- Stages: `init → from_city → to_city → date → budget → time → confirm → results_shown`.
- Local Parsing:
  - Route: phrases like "karachi se lahore", or destination cues like "lahore jana".
  - Date: `aaj / kal / parso`, `YYYY-MM-DD`, or `DD/MM/YYYY`.
  - Time window: `subah | dopahar | raat` (with common English synonyms mapped).
  - Budget/Class: numeric `Rs. ####` or keywords `Economy | Business | AC`.
  - Format: `list | table | json` (optional).
- LLM Assist (optional): Up to 2 calls to extract JSON fields; disabled automatically if no key or provider error.
- Confirmation: Once all required fields present, asks for confirmation; on "haan" proceeds to search and formats results.

Required Fields Before Search
- `from_station`, `to_station`, `travel_date`, `preferred_time`, `budget`.

Extending The Flow
- Add a field:
  1) Update local extractors in `ai_agent.py`.
  2) Include it in `_has_all_required` if it’s mandatory.
  3) Adjust messages (`_ask_*`, `_confirm_message`) and `_llm_extract` schema.
  4) Pass it through to `PakRailScraper` (if needed) and update result formatting.

## Scraper: Behavior & Data
- Attempts Selenium with headless Chrome (container-friendly), but currently returns realistic sample data for stability.
- Filters results by time preference (`subah`, `dopahar`, `raat`).
- Persists synthetic results to `data/train_data.json` via `DataManager` for inspection/debugging.
- Always calls `cleanup()` to close resources (driver/session).

## Frontend: Behavior
- Simple chat UI with message list and input box.
- Hits `POST /api/chat` with stored `sessionId` (from `localStorage`) to preserve conversation.
- "+ New Chat" button triggers `/api/reset` and clears session.
- Configure API base with `VITE_API_BASE`.

## Deployment
- Dockerfile builds the React frontend, copies build into `/app/static`, and runs FastAPI via `uvicorn app_entry:app` on `${PORT:-7860}`.
- `docker-compose.yml` exposes `7860` and runs in `--reload` for convenience.

## Logging & Errors
- Use `modules.utils.Logger` for `info`, `warning`, `error` across modules.
- Agent and scraper degrade gracefully; user sees friendly errors and can type `reset` to start over.

## Development Rules (for LLMs & Humans)
- Keep changes minimal and surgical; maintain public APIs and filenames unless explicitly changing design.
- Use type hints and small, well-named functions.
- Preserve Roman-Urdu polite tone in user-facing text in `ai_agent.py`.
- If you change endpoints or payloads, update this guide and the frontend fetch logic in `frontend/src/App.jsx`.
- Don’t introduce persistent global state; server sessions are in-memory and ephemeral.

## Repo Map (Key Paths)
- `Railway_Fair_finder/server.py` — FastAPI routes: `/api/health`, `/api/chat`, `/api/reset`.
- `Railway_Fair_finder/app_entry.py` — Wraps API app, mounts static build.
- `Railway_Fair_finder/modules/ai_agent.py` — FSM + parsing + optional LLM calls.
- `Railway_Fair_finder/modules/scraper.py` — Selenium/requests scaffolding with sample data.
- `Railway_Fair_finder/config/settings.py` — dotenv config (API key, timeouts, model).
- `Railway_Fair_finder/frontend/` — Vite React UI (scripts: `dev`, `build`, `preview`).
- `Railway_Fair_finder/Dockerfile`, `Railway_Fair_finder/docker-compose.yml` — containerized full stack.

## Troubleshooting
- Garbled glyphs in some CLI/UI strings (e.g., `main.py`) are cosmetic; safe to ignore. They can be cleaned up later.
- If `/api/chat` returns errors, check backend logs and ensure CORS is permissive in dev (`allow_origins=["*"]`).
- If LLM calls hang/fail, remove `OPENROUTER_API_KEY` or accept offline mode; local parsing covers common phrases.

— End of single-file guide —

