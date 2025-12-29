"""Message model for database persistence."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Message:
    """Represents a chat message."""
    id: str
    chat_id: str
    role: str  # 'user' or 'assistant'
    content: str
    created_at: str

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "chat_id": self.chat_id,
            "role": self.role,
            "content": self.content,
            "created_at": self.created_at,
        }
