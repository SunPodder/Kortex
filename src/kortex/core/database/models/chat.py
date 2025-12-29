"""Chat model for database persistence."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Chat:
    """Represents a chat conversation."""
    id: str
    title: str
    created_at: str
    updated_at: str
    model: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "model": self.model,
        }
