import redis
import json
from datetime import datetime

# Connect to Redis
r = redis.Redis(host="localhost", port=6379, decode_responses=True)


def save_message(session_id: str, role: str, content: str):
    """Save a message to session history"""
    message = {
        "role": role,
        "content": content,
        "timestamp": datetime.now().isoformat()
    }
    # Append to a list in Redis using session_id as key
    r.rpush(session_id, json.dumps(message))
    # Expire session after 2 hours of inactivity
    r.expire(session_id, 7200)


def get_history(session_id: str) -> list:
    """Get full conversation history for a session"""
    messages = r.lrange(session_id, 0, -1)
    return [json.loads(m) for m in messages]


def get_context_summary(session_id: str) -> str:
    """Build a summary of conversation history for LLM context"""
    history = get_history(session_id)

    if not history:
        return "No previous conversation in this session."

    lines = []
    for msg in history:
        role = "User" if msg["role"] == "user" else "CodeMind"
        lines.append(f"{role}: {msg['content']}")

    return "\n".join(lines)


def clear_session(session_id: str):
    """Clear session history"""
    r.delete(session_id)