import os
# Need to set USER_AGENT before importing config
os.environ.setdefault("USER_AGENT", "RailwayFareAgent/1.0 (+http://localhost:8000)")

import json
import re
import asyncio
from datetime import datetime
from fastapi import FastAPI
from config import logger, OPENROUTER_API_KEY
from models import QueryRequest, FareResponse
from memory import get_user_memory, user_memories
from agent import create_railway_agent

# FastAPI app
app = FastAPI(title="Railway Fare Agent", description="AI Agent for Pakistan Railway Fare Search")

# -----------------------------------------------------------------------------------
# Initialize agent
# -----------------------------------------------------------------------------------

agent_executor = create_railway_agent(OPENROUTER_API_KEY)

# -----------------------------------------------------------------------------------
# API Endpoints
# -----------------------------------------------------------------------------------

@app.post("/search", response_model=FareResponse)
async def search_fares(request: QueryRequest):
    """Main endpoint for railway fare searches"""
    try:
        # Get user memory
        memory = get_user_memory(request.user_id)

        # Process query with agent
        result = await asyncio.to_thread(
            agent_executor.invoke,
            {
                "input": request.query,
                "chat_history": memory.chat_memory.messages
            }
        )

        # Update memory
        memory.save_context(
            {"input": request.query},
            {"output": result["output"]}
        )

        # Try to parse JSON from result
        try:
            output_text = result["output"]
            if "```json" in output_text:
                json_str = output_text.split("```json")[1].split("```")[0]
                parsed_data = json.loads(json_str)
            else:
                # Look for JSON in the output
                json_match = re.search(r'\{.*\}', output_text, re.DOTALL)
                if json_match:
                    parsed_data = json.loads(json_match.group())
                else:
                    parsed_data = {"message": output_text}
        except Exception:
            parsed_data = {"message": result["output"]}

        # Check if input is required
        requires_input = parsed_data.get("requires_input", False)
        missing_fields = parsed_data.get("missing_fields", [])

        return FareResponse(
            success=not ("error" in parsed_data),
            data=parsed_data,
            message=parsed_data.get("message", result["output"]),
            requires_input=requires_input,
            missing_fields=missing_fields
        )

    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        return FareResponse(
            success=False,
            message=f"Search failed: {str(e)}"
        )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.delete("/memory/{user_id}")
async def clear_user_memory(user_id: str):
    """Clear conversation memory for a user"""
    if user_id in user_memories:
        del user_memories[user_id]
        return {"message": f"Memory cleared for user {user_id}"}
    return {"message": f"No memory found for user {user_id}"}