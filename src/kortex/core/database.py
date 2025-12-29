"""SQLite database module for chat persistence."""
from __future__ import annotations

import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


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


class ChatDatabase:
    """SQLite database for storing chats and messages."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        if db_path is None:
            # Default to user's data directory
            data_dir = Path.home() / ".local" / "share" / "kortex"
            data_dir.mkdir(parents=True, exist_ok=True)
            db_path = data_dir / "chats.db"
        
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection with row factory."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Initialize the database schema."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            # Create chats table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chats (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    model TEXT DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            
            # Create messages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    chat_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (chat_id) REFERENCES chats(id) ON DELETE CASCADE
                )
            """)
            
            # Create index for faster message retrieval
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_chat_id 
                ON messages(chat_id)
            """)
            
            conn.commit()
        finally:
            conn.close()

    def create_chat(self, title: str = "New conversation", model: str = "") -> Chat:
        """Create a new chat."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            chat_id = str(uuid.uuid4())
            now = datetime.now().isoformat()
            
            cursor.execute(
                """
                INSERT INTO chats (id, title, model, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (chat_id, title, model, now, now)
            )
            
            conn.commit()
            
            return Chat(
                id=chat_id,
                title=title,
                model=model,
                created_at=now,
                updated_at=now,
            )
        finally:
            conn.close()

    def get_chat(self, chat_id: str) -> Optional[Chat]:
        """Get a chat by ID."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM chats WHERE id = ?", (chat_id,))
            row = cursor.fetchone()
            
            if row:
                return Chat(
                    id=row["id"],
                    title=row["title"],
                    model=row["model"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
            return None
        finally:
            conn.close()

    def get_all_chats(self) -> list[Chat]:
        """Get all chats, ordered by most recent first."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM chats ORDER BY updated_at DESC"
            )
            rows = cursor.fetchall()
            
            return [
                Chat(
                    id=row["id"],
                    title=row["title"],
                    model=row["model"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
                for row in rows
            ]
        finally:
            conn.close()

    def update_chat(self, chat_id: str, title: Optional[str] = None, model: Optional[str] = None) -> bool:
        """Update a chat's title and/or model."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            updates = []
            params = []
            
            if title is not None:
                updates.append("title = ?")
                params.append(title)
            
            if model is not None:
                updates.append("model = ?")
                params.append(model)
            
            if not updates:
                return False
            
            updates.append("updated_at = ?")
            params.append(datetime.now().isoformat())
            params.append(chat_id)
            
            cursor.execute(
                f"UPDATE chats SET {', '.join(updates)} WHERE id = ?",
                params
            )
            
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def delete_chat(self, chat_id: str) -> bool:
        """Delete a chat and all its messages."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            # Delete messages first
            cursor.execute("DELETE FROM messages WHERE chat_id = ?", (chat_id,))
            
            # Delete chat
            cursor.execute("DELETE FROM chats WHERE id = ?", (chat_id,))
            
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def add_message(self, chat_id: str, role: str, content: str) -> Message:
        """Add a message to a chat."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            message_id = str(uuid.uuid4())
            now = datetime.now().isoformat()
            
            cursor.execute(
                """
                INSERT INTO messages (id, chat_id, role, content, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (message_id, chat_id, role, content, now)
            )
            
            # Update chat's updated_at timestamp
            cursor.execute(
                "UPDATE chats SET updated_at = ? WHERE id = ?",
                (now, chat_id)
            )
            
            conn.commit()
            
            return Message(
                id=message_id,
                chat_id=chat_id,
                role=role,
                content=content,
                created_at=now,
            )
        finally:
            conn.close()

    def get_messages(self, chat_id: str) -> list[Message]:
        """Get all messages for a chat, ordered by creation time."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM messages WHERE chat_id = ? ORDER BY created_at ASC",
                (chat_id,)
            )
            rows = cursor.fetchall()
            
            return [
                Message(
                    id=row["id"],
                    chat_id=row["chat_id"],
                    role=row["role"],
                    content=row["content"],
                    created_at=row["created_at"],
                )
                for row in rows
            ]
        finally:
            conn.close()

    def get_last_message(self, chat_id: str) -> Optional[Message]:
        """Get the last message in a chat."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM messages WHERE chat_id = ? ORDER BY created_at DESC LIMIT 1",
                (chat_id,)
            )
            row = cursor.fetchone()
            
            if row:
                return Message(
                    id=row["id"],
                    chat_id=row["chat_id"],
                    role=row["role"],
                    content=row["content"],
                    created_at=row["created_at"],
                )
            return None
        finally:
            conn.close()

    def generate_chat_title(self, chat_id: str) -> str:
        """Generate a title based on the first user message."""
        messages = self.get_messages(chat_id)
        
        for msg in messages:
            if msg.role == "user":
                # Take first 50 chars of the first user message
                title = msg.content[:50]
                if len(msg.content) > 50:
                    title += "..."
                return title
        
        return "New conversation"
