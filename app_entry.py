# app_entry.py
import os
import logging
import importlib
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app_entry")

# 1) Try to import the real API from common module paths
api = None
candidates = [
    # Local/simple
    "server:app",
    "main:app",
    "app:app",
    # Backend-style
    "backend.server:app",
    "backend.main:app",
    # Monorepo-style (as per your guide)
    "Railway_Fair_finder.server:app",
    "Railway_Fair_finder.main:app",
]

for candidate in candidates:
    try:
        module_name, obj_name = candidate.split(":")
        module = importlib.import_module(module_name)
        api = getattr(module, obj_name, None)
        if api is None:
            raise AttributeError(f"{candidate} found module but no 'app'")
        logger.info(f"Loaded API from {candidate}")
        break
    except Exception as e:
        logger.debug(f"Failed to load {candidate}: {e}")
        continue

if api is None:
    # Minimal fallback API to keep container healthy if import fails
    from fastapi import FastAPI as _F
    _fallback = _F()

    @_fallback.get("/api/health")
    def _health():
        return {"ok": True, "note": "fallback API stub"}
    api = _fallback
    logger.warning("Falling back to stub API (could not import real API app)")

# Create the outer app that will serve API + static
app = FastAPI()

# 2) Copy middleware and overrides from the actual API app
if hasattr(api, "user_middleware"):
    for m in api.user_middleware:
        # Starlette version differences
        options = getattr(m, "options", None) or getattr(m, "kwargs", None) or {}
        args = getattr(m, "args", ()) or ()
        app.add_middleware(m.cls, *args, **options)

if hasattr(api, "dependency_overrides"):
    app.dependency_overrides.update(api.dependency_overrides)

# Prefer including the API router directly if present; otherwise mount under /api
if hasattr(api, "router") and getattr(api, "router") is not None:
    app.include_router(api.router)
    # Copy startup/shutdown hooks if any
    for h in getattr(api.router, "on_startup", []):
        app.router.on_startup.append(h)
    for h in getattr(api.router, "on_shutdown", []):
        app.router.on_shutdown.append(h)
else:
    # Fallback mount (works if 'api' is an ASGI app)
    app.mount("/api", api)

# 3) Serve built frontend (Vite) from / (SPA fallback)
STATIC_DIR = os.path.abspath(os.getenv("STATIC_DIR", "static"))
if os.path.isdir(STATIC_DIR):
    logger.info(f"Serving static from {STATIC_DIR}")
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
else:
    logger.warning(f"STATIC_DIR not found: {STATIC_DIR} (frontend not mounted)")