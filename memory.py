from typing import Dict
from langchain.memory import ConversationBufferMemory

# -----------------------------------------------------------------------------------
# Memory management for user sessions
# -----------------------------------------------------------------------------------

user_memories: Dict[str, ConversationBufferMemory] = {}

def get_user_memory(user_id: str) -> ConversationBufferMemory:
    if user_id not in user_memories:
        user_memories[user_id] = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
    return user_memories[user_id]