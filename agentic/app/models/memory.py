"""
Conversation Memory
Same as structured RAG - session-based memory
"""
class Memory:
    _sessions = {}

    @classmethod
    def add_turn(cls, session_id: str, user_msg: str, assistant_msg: str):
        """Add a conversation turn to a session"""
        if session_id not in cls._sessions:
            cls._sessions[session_id] = []
        cls._sessions[session_id].append((user_msg, assistant_msg))

    @classmethod
    def get_context(cls, session_id: str, max_turns: int = 6) -> str:
        """Get conversation history for a session as formatted string"""
        if session_id not in cls._sessions or not cls._sessions[session_id]:
            return ""
        
        history = cls._sessions[session_id][-max_turns:]
        return "\n".join([f"User: {u}\nAssistant: {a}" for u, a in history])

    @classmethod
    def clear_session(cls, session_id: str):
        """Clear conversation history for a specific session"""
        if session_id in cls._sessions:
            cls._sessions[session_id] = []

    @classmethod
    def clear_all(cls):
        """Clear all session histories"""
        cls._sessions = {}

