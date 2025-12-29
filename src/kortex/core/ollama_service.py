"""Ollama integration service for AI chat functionality."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Generator, Optional

import ollama
from ollama import Client

logger = logging.getLogger(__name__)


@dataclass
class OllamaModel:
    """Represents an Ollama model."""
    name: str
    size: int
    modified_at: str
    digest: str

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "size": self.size,
            "modified_at": self.modified_at,
            "digest": self.digest,
        }


@dataclass 
class ChatMessage:
    """Represents a message in a chat conversation."""
    role: str  # 'user', 'assistant', or 'system'
    content: str


class OllamaService:
    """Service for interacting with Ollama API."""

    def __init__(self, host: str = "http://localhost:11434") -> None:
        self.host = host
        self._client = Client(host=host)
        self._loaded_model: Optional[str] = None

    def is_available(self) -> bool:
        """Check if Ollama server is running and accessible."""
        try:
            self._client.list()
            return True
        except Exception as e:
            logger.warning(f"Ollama server not available: {e}")
            return False

    def list_models(self) -> list[OllamaModel]:
        """List all available Ollama models."""
        try:
            response = self._client.list()
            models = []
            
            # Handle both dict response and object response
            model_list = response.get("models", []) if isinstance(response, dict) else getattr(response, "models", [])
            
            for model in model_list:
                if isinstance(model, dict):
                    models.append(OllamaModel(
                        name=model.get("name", ""),
                        size=model.get("size", 0),
                        modified_at=model.get("modified_at", ""),
                        digest=model.get("digest", ""),
                    ))
                else:
                    # Handle object response
                    models.append(OllamaModel(
                        name=getattr(model, "model", "") or getattr(model, "name", ""),
                        size=getattr(model, "size", 0),
                        modified_at=str(getattr(model, "modified_at", "")),
                        digest=getattr(model, "digest", ""),
                    ))
            
            return models
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []

    def get_model_names(self) -> list[str]:
        """Get a list of available model names."""
        models = self.list_models()
        return [model.name for model in models]

    def ensure_model_loaded(self, model_name: str) -> bool:
        """Ensure a model is loaded and ready."""
        if self._loaded_model == model_name:
            return True

        try:
            # Send an empty generate request to load the model
            # This is a lightweight way to ensure the model is loaded
            self._client.generate(model=model_name, prompt="", keep_alive="5m")
            self._loaded_model = model_name
            logger.info(f"Model '{model_name}' loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to load model '{model_name}': {e}")
            return False

    def chat(
        self,
        model: str,
        messages: list[ChatMessage],
        stream: bool = False,
    ) -> str:
        """Send a chat message and get a response."""
        try:
            # Ensure model is loaded
            if not self.ensure_model_loaded(model):
                return "Error: Failed to load the model. Please check if Ollama is running."

            # Convert messages to dict format
            message_dicts = [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ]

            if stream:
                # For streaming, collect all chunks
                full_response = ""
                for chunk in self._client.chat(
                    model=model,
                    messages=message_dicts,
                    stream=True,
                ):
                    # Handle both dict and object response
                    if isinstance(chunk, dict):
                        if "message" in chunk and "content" in chunk["message"]:
                            full_response += chunk["message"]["content"]
                    else:
                        message = getattr(chunk, "message", None)
                        if message:
                            content = getattr(message, "content", "")
                            full_response += content
                return full_response
            else:
                # Non-streaming response
                response = self._client.chat(
                    model=model,
                    messages=message_dicts,
                    stream=False,
                )
                # Handle both dict and object response
                if isinstance(response, dict):
                    return response.get("message", {}).get("content", "")
                else:
                    message = getattr(response, "message", None)
                    if message:
                        return getattr(message, "content", "")
                    return ""

        except Exception as e:
            logger.error(f"Chat error: {e}")
            return f"Error: {str(e)}"

    def chat_stream(
        self,
        model: str,
        messages: list[ChatMessage],
    ) -> Generator[str, None, None]:
        """Stream a chat response."""
        try:
            # Ensure model is loaded
            if not self.ensure_model_loaded(model):
                yield "Error: Failed to load the model. Please check if Ollama is running."
                return

            # Convert messages to dict format
            message_dicts = [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ]

            for chunk in self._client.chat(
                model=model,
                messages=message_dicts,
                stream=True,
            ):
                # Handle both dict and object response
                if isinstance(chunk, dict):
                    if "message" in chunk and "content" in chunk["message"]:
                        yield chunk["message"]["content"]
                else:
                    message = getattr(chunk, "message", None)
                    if message:
                        content = getattr(message, "content", "")
                        if content:
                            yield content

        except Exception as e:
            logger.error(f"Chat stream error: {e}")
            yield f"Error: {str(e)}"

    def pull_model(self, model_name: str) -> Generator[dict, None, None]:
        """Pull/download a model from Ollama registry."""
        try:
            for progress in self._client.pull(model_name, stream=True):
                yield progress
        except Exception as e:
            logger.error(f"Failed to pull model '{model_name}': {e}")
            yield {"error": str(e)}
