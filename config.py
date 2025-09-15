import os

# Set USER_AGENT before any DuckDuckGo imports to avoid warnings
os.environ.setdefault("USER_AGENT", "RailwayFareAgent/1.0 (+http://localhost:8000)")
# Map OpenRouter settings to OpenAI-compatible env vars used by langchain-openai
if os.getenv("OPENROUTER_API_KEY") and not os.getenv("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENROUTER_API_KEY")
os.environ.setdefault("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")

import logging

# -----------------------------------------------------------------------------------
# Configuration & Logging
# -----------------------------------------------------------------------------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")