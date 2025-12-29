"""Chat controller for bridging Python backend with QML frontend."""
from __future__ import annotations

import logging
from typing import Optional

from PySide6.QtCore import QObject, Property, Signal, Slot, QThread

from kortex.core.database import ChatDatabase
from kortex.core.ollama_service import OllamaService, ChatMessage

logger = logging.getLogger(__name__)


class ChatWorker(QThread):
    """Worker thread for handling chat requests."""
    
    response_ready = Signal(str, str)  # chat_id, response
    response_chunk = Signal(str, str)  # chat_id, chunk (for streaming)
    response_error = Signal(str, str)  # chat_id, error message
    
    def __init__(
        self,
        ollama_service: OllamaService,
        model: str,
        messages: list[ChatMessage],
        chat_id: str,
    ) -> None:
        super().__init__()
        self._ollama_service = ollama_service
        self._model = model
        self._messages = messages
        self._chat_id = chat_id
    
    def run(self) -> None:
        """Execute the chat request."""
        try:
            response = self._ollama_service.chat(
                model=self._model,
                messages=self._messages,
                stream=False,
            )
            self.response_ready.emit(self._chat_id, response)
        except Exception as e:
            logger.error(f"Chat worker error: {e}")
            self.response_error.emit(self._chat_id, str(e))


class TitleGeneratorWorker(QThread):
    """Worker thread for generating chat titles in the background."""
    
    title_ready = Signal(str, str)  # chat_id, title
    
    def __init__(
        self,
        ollama_service: OllamaService,
        model: str,
        user_message: str,
        chat_id: str,
    ) -> None:
        super().__init__()
        self._ollama_service = ollama_service
        self._model = model
        self._user_message = user_message
        self._chat_id = chat_id
    
    def run(self) -> None:
        """Generate a title for the chat."""
        try:
            # Create a system prompt for title generation
            messages = [
                ChatMessage(
                    role="system",
                    content="Generate a very short, concise title (3-6 words max) for a conversation that starts with the following message. Only output the title, nothing else. No quotes, no explanations."
                ),
                ChatMessage(
                    role="user",
                    content=f"Generate a title for a conversation starting with: \"{self._user_message[:200]}\""
                ),
            ]
            
            response = self._ollama_service.chat(
                model=self._model,
                messages=messages,
                stream=False,
            )
            
            # Clean up the title
            title = response.strip().strip('"').strip("'")
            if len(title) > 50:
                title = title[:47] + "..."
            
            if title:
                self.title_ready.emit(self._chat_id, title)
            else:
                # Fallback to truncated message
                fallback = self._user_message[:50]
                if len(self._user_message) > 50:
                    fallback += "..."
                self.title_ready.emit(self._chat_id, fallback)
                
        except Exception as e:
            logger.error(f"Title generation error: {e}")
            # Fallback to truncated message on error
            fallback = self._user_message[:50]
            if len(self._user_message) > 50:
                fallback += "..."
            self.title_ready.emit(self._chat_id, fallback)


class ChatController(QObject):
    """Controller for managing chats and messages."""
    
    # Signals
    chatsChanged = Signal()
    messagesChanged = Signal()
    modelsChanged = Signal()
    currentChatChanged = Signal()
    isLoadingChanged = Signal()
    responseReceived = Signal(str, str)  # chat_id, response
    
    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        
        self._db = ChatDatabase()
        self._ollama = OllamaService()
        self._current_chat_id: Optional[str] = None
        self._is_loading = False
        self._worker: Optional[ChatWorker] = None
        self._title_worker: Optional[TitleGeneratorWorker] = None
        self._models: list[str] = []
        self._current_model: str = ""
        
        # Load available models
        self._refresh_models()
    
    # Properties
    @Property(bool, notify=isLoadingChanged)
    def isLoading(self) -> bool:
        return self._is_loading
    
    @isLoading.setter
    def isLoading(self, value: bool) -> None:
        if self._is_loading != value:
            self._is_loading = value
            self.isLoadingChanged.emit()
    
    @Property(str, notify=currentChatChanged)
    def currentChatId(self) -> str:
        return self._current_chat_id or ""
    
    @currentChatId.setter
    def currentChatId(self, value: str) -> None:
        if self._current_chat_id != value:
            self._current_chat_id = value if value else None
            self.currentChatChanged.emit()
            self.messagesChanged.emit()
    
    @Property(str, notify=modelsChanged)
    def currentModel(self) -> str:
        return self._current_model
    
    @currentModel.setter
    def currentModel(self, value: str) -> None:
        if self._current_model != value:
            self._current_model = value
            # Update current chat's model if exists
            if self._current_chat_id:
                self._db.update_chat(self._current_chat_id, model=value)
            self.modelsChanged.emit()
    
    # Slots
    @Slot(result=list)
    def getChats(self) -> list:
        """Get all chats with preview info."""
        chats = self._db.get_all_chats()
        result = []
        
        for chat in chats:
            last_message = self._db.get_last_message(chat.id)
            preview = ""
            if last_message:
                preview = last_message.content[:50]
                if len(last_message.content) > 50:
                    preview += "..."
            
            result.append({
                "id": chat.id,
                "title": chat.title,
                "preview": preview,
                "model": chat.model,
            })
        
        return result
    
    @Slot(result=list)
    def getModels(self) -> list:
        """Get list of available Ollama models."""
        return self._models
    
    @Slot()
    def refreshModels(self) -> None:
        """Refresh the list of available models."""
        self._refresh_models()
    
    def _refresh_models(self) -> None:
        """Internal method to refresh models."""
        if self._ollama.is_available():
            self._models = self._ollama.get_model_names()
            if self._models and not self._current_model:
                self._current_model = self._models[0]
        else:
            self._models = []
            logger.warning("Ollama is not available")
        
        self.modelsChanged.emit()
    
    @Slot(result=str)
    def createChat(self) -> str:
        """Create a new chat and return its ID."""
        chat = self._db.create_chat(model=self._current_model)
        self._current_chat_id = chat.id
        self.chatsChanged.emit()
        self.currentChatChanged.emit()
        self.messagesChanged.emit()
        return chat.id
    
    @Slot(str)
    def deleteChat(self, chat_id: str) -> None:
        """Delete a chat."""
        self._db.delete_chat(chat_id)
        
        if self._current_chat_id == chat_id:
            # Select another chat or None
            chats = self._db.get_all_chats()
            if chats:
                self._current_chat_id = chats[0].id
            else:
                self._current_chat_id = None
            self.currentChatChanged.emit()
            self.messagesChanged.emit()
        
        self.chatsChanged.emit()
    
    @Slot(str)
    def selectChat(self, chat_id: str) -> None:
        """Select a chat as current."""
        self.currentChatId = chat_id
        
        # Update current model to match chat's model
        chat = self._db.get_chat(chat_id)
        if chat and chat.model:
            self._current_model = chat.model
            self.modelsChanged.emit()
    
    @Slot(str, result=list)
    def getMessages(self, chat_id: str) -> list:
        """Get all messages for a chat."""
        messages = self._db.get_messages(chat_id)
        return [
            {
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "isUser": msg.role == "user",
            }
            for msg in messages
        ]
    
    @Slot(str, str)
    def sendMessage(self, chat_id: str, content: str) -> None:
        """Send a message and get AI response."""
        if not content.strip():
            return
        
        if self._is_loading:
            return
        
        # Create chat if needed
        if not chat_id:
            chat_id = self.createChat()
        
        # Add user message to database
        self._db.add_message(chat_id, "user", content)
        self.messagesChanged.emit()
        
        # Check if this is the first message - set temporary title
        messages = self._db.get_messages(chat_id)
        is_first_message = len(messages) == 1
        
        if is_first_message:
            # Set a temporary title immediately so chat appears in sidebar
            temp_title = content[:50]
            if len(content) > 50:
                temp_title += "..."
            self._db.update_chat(chat_id, title=temp_title)
            self.chatsChanged.emit()
        
        # Check if Ollama is available
        if not self._ollama.is_available():
            self._db.add_message(
                chat_id, 
                "assistant", 
                "Error: Ollama is not running. Please start Ollama and try again."
            )
            self.messagesChanged.emit()
            return
        
        # Check if we have a model selected
        if not self._current_model:
            if self._models:
                self._current_model = self._models[0]
            else:
                self._db.add_message(
                    chat_id,
                    "assistant",
                    "Error: No models available. Please pull a model using 'ollama pull <model-name>'."
                )
                self.messagesChanged.emit()
                return
        
        # Start loading
        self.isLoading = True
        
        # Prepare messages for Ollama
        chat_messages = [
            ChatMessage(role=msg.role, content=msg.content)
            for msg in messages
        ]
        
        # Create and start worker thread
        self._worker = ChatWorker(
            ollama_service=self._ollama,
            model=self._current_model,
            messages=chat_messages,
            chat_id=chat_id,
        )
        self._worker.response_ready.connect(self._on_response_ready)
        self._worker.response_error.connect(self._on_response_error)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.start()
    
    def _start_title_generation(self, chat_id: str, user_message: str) -> None:
        """Start background title generation."""
        self._title_worker = TitleGeneratorWorker(
            ollama_service=self._ollama,
            model=self._current_model,
            user_message=user_message,
            chat_id=chat_id,
        )
        self._title_worker.title_ready.connect(self._on_title_ready)
        self._title_worker.finished.connect(self._on_title_worker_finished)
        self._title_worker.start()
    
    def _on_title_ready(self, chat_id: str, title: str) -> None:
        """Handle generated title from background worker."""
        logger.info(f"Generated title for chat {chat_id}: {title}")
        self._db.update_chat(chat_id, title=title)
        self.chatsChanged.emit()
    
    def _on_title_worker_finished(self) -> None:
        """Clean up title worker after it finishes."""
        if self._title_worker:
            self._title_worker.deleteLater()
            self._title_worker = None
    
    def _on_response_ready(self, chat_id: str, response: str) -> None:
        """Handle response from Ollama."""
        self._db.add_message(chat_id, "assistant", response)
        self.messagesChanged.emit()
        self.chatsChanged.emit()  # Update preview
        self.responseReceived.emit(chat_id, response)
        
        # Generate title in background after response is served (only for first message)
        messages = self._db.get_messages(chat_id)
        # Check if this was the first user message (2 messages = 1 user + 1 assistant)
        if len(messages) == 2:
            user_message = messages[0].content
            if self._ollama.is_available() and self._current_model:
                self._start_title_generation(chat_id, user_message)
    
    def _on_response_error(self, chat_id: str, error: str) -> None:
        """Handle error from Ollama."""
        self._db.add_message(chat_id, "assistant", f"Error: {error}")
        self.messagesChanged.emit()
    
    def _on_worker_finished(self) -> None:
        """Clean up after worker finishes."""
        self.isLoading = False
        if self._worker:
            self._worker.deleteLater()
            self._worker = None
    
    @Slot(str)
    def setModel(self, model_name: str) -> None:
        """Set the current model."""
        self.currentModel = model_name
    
    @Slot(result=bool)
    def isOllamaAvailable(self) -> bool:
        """Check if Ollama is available."""
        return self._ollama.is_available()
