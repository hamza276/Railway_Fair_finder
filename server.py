# server.py
import uuid
from typing import Optional, Dict
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from modules.ai_agent import TrainBookingAI  # ensure import path is correct

app = FastAPI(title="PakRail AI Chat API")

# CORS for local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # in prod set specific origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session store: session_id -> TrainBookingAI instance
SESSIONS: Dict[str, TrainBookingAI] = {}

class ChatRequest(BaseModel):
    message: str
    sessionId: Optional[str] = None

class ChatResponse(BaseModel):
    reply: str
    sessionId: str

class ResetRequest(BaseModel):
    sessionId: Optional[str] = None

@app.get("/api/health")
def health():
    return {"status": "ok"}

@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    session_id = req.sessionId or str(uuid.uuid4())
    if session_id not in SESSIONS:
        SESSIONS[session_id] = TrainBookingAI()
    agent = SESSIONS[session_id]

    reply = agent.process_user_input(req.message or "")
    return ChatResponse(reply=reply, sessionId=session_id)

@app.post("/api/reset")
def reset(req: ResetRequest):
    if req.sessionId and req.sessionId in SESSIONS:
        try:
            # call agent reset for cleanup
            SESSIONS[req.sessionId].reset_conversation()
        except:
            pass
        del SESSIONS[req.sessionId]
    return {"ok": True}

