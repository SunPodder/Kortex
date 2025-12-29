"""Chat controller for bridging Python backend with QML frontend."""
from __future__ import annotations

import json
import logging
import uuid
from typing import Optional

from PySide6.QtCore import QObject, Property, Signal, Slot, QThread

from kortex.core.database import KortexDatabase
from kortex.core.ollama_service import OllamaService, ChatMessage
from kortex.core.agent import (
    AgentService,
    AgentState,
    get_agent_service,
    check_required_models,
    REQUIRED_AGENT_MODELS,
    ROUTER_MODEL,
    TOOL_MODEL,
)
from kortex.core.tools import ToolCall, ToolResult, tool_registry, Permission

logger = logging.getLogger(__name__)


class AgentWorker(QThread):
    """Worker thread for handling agent requests with tool calling."""
    
    response_ready = Signal(str, str, list)  # chat_id, response, pending_tool_calls
    response_chunk = Signal(str, str)  # chat_id, chunk (for streaming)
    response_error = Signal(str, str)  # chat_id, error message
    tool_calls_ready = Signal(str, list)  # chat_id, list of tool call dicts
    
    def __init__(
        self,
        agent_service: AgentService,
        user_message: str,
        chat_id: str,
        history: list[dict],
        state: AgentState,
    ) -> None:
        super().__init__()
        self._agent_service = agent_service
        self._user_message = user_message
        self._chat_id = chat_id
        self._history = history
        self._state = state
    
    def run(self) -> None:
        """Execute the agent request."""
        try:
            response, pending_calls, updated_state = self._agent_service.process_message(
                self._user_message,
                self._state,
                self._history,
            )
            
            # Convert tool calls to serializable dicts
            tool_call_dicts = [tc.to_dict() for tc in pending_calls]
            
            self.response_ready.emit(self._chat_id, response, tool_call_dicts)
            
        except Exception as e:
            logger.error(f"Agent worker error: {e}")
            self.response_error.emit(self._chat_id, str(e))


class ToolExecutionWorker(QThread):
    """Worker thread for executing tool calls."""
    
    execution_complete = Signal(str, str, list)  # chat_id, response, new_pending_tool_calls
    execution_error = Signal(str, str)  # chat_id, error message
    
    def __init__(
        self,
        agent_service: AgentService,
        chat_id: str,
        state: AgentState,
        approved_ids: set[str],
        denied_ids: set[str],
        user_message: str = "",
        history: list[dict] = None,
    ) -> None:
        super().__init__()
        self._agent_service = agent_service
        self._chat_id = chat_id
        self._state = state
        self._approved_ids = approved_ids
        self._denied_ids = denied_ids
        self._user_message = user_message
        self._history = history or []
    
    def run(self) -> None:
        """Execute the tool calls."""
        try:
            response, new_pending, updated_state = self._agent_service.execute_tool_calls(
                self._state,
                approved_call_ids=self._approved_ids,
                denied_call_ids=self._denied_ids,
                user_message=self._user_message,
                history=self._history,
            )
            
            tool_call_dicts = [tc.to_dict() for tc in new_pending]
            self.execution_complete.emit(self._chat_id, response, tool_call_dicts)
            
        except Exception as e:
            logger.error(f"Tool execution worker error: {e}")
            self.execution_error.emit(self._chat_id, str(e))


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
    
    # Agent-related signals
    toolCallsPending = Signal(str, list)  # chat_id, list of tool call dicts
    agentModeChanged = Signal()
    agentModelsAvailableChanged = Signal()
    
    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        
        self._db = KortexDatabase()
        self._ollama = OllamaService()
        self._current_chat_id: Optional[str] = None
        self._is_loading = False
        self._agent_mode = False  # Start disabled until models are verified
        self._agent_models_available = False
        self._missing_agent_models: list[str] = []
        self._worker: Optional[ChatWorker] = None
        self._agent_worker: Optional[AgentWorker] = None
        self._tool_worker: Optional[ToolExecutionWorker] = None
        self._title_worker: Optional[TitleGeneratorWorker] = None
        self._models: list[str] = []
        self._current_model: str = ""
        
        # Agent state per chat
        self._agent_states: dict[str, AgentState] = {}
        self._pending_tool_calls: dict[str, list[dict]] = {}
        # Store user messages for context during tool execution
        self._user_messages: dict[str, str] = {}
        
        # Load available models
        self._refresh_models()
    
    def _get_agent_service(self) -> AgentService:
        """Get the agent service with current model."""
        return get_agent_service(self._current_model, self._ollama.host)
    
    def _get_or_create_agent_state(self, chat_id: str) -> AgentState:
        """Get or create agent state for a chat."""
        if chat_id not in self._agent_states:
            self._agent_states[chat_id] = self._get_agent_service().create_state()
        return self._agent_states[chat_id]
    
    # Properties
    @Property(bool, notify=isLoadingChanged)
    def isLoading(self) -> bool:
        return self._is_loading
    
    @isLoading.setter
    def isLoading(self, value: bool) -> None:
        if self._is_loading != value:
            self._is_loading = value
            self.isLoadingChanged.emit()
    
    @Property(bool, notify=agentModeChanged)
    def agentMode(self) -> bool:
        return self._agent_mode
    
    @agentMode.setter
    def agentMode(self, value: bool) -> None:
        if self._agent_mode != value:
            self._agent_mode = value
            self.agentModeChanged.emit()
    
    @Property(bool, notify=agentModelsAvailableChanged)
    def agentModelsAvailable(self) -> bool:
        return self._agent_models_available
    
    @Property(list, notify=agentModelsAvailableChanged)
    def missingAgentModels(self) -> list:
        return self._missing_agent_models
    
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
            
            # Check if required agent models are available
            available, missing = check_required_models(self._models)
            self._agent_models_available = available
            self._missing_agent_models = missing
            
            if not available:
                logger.warning(f"Agent mode requires models: {missing}")
                # Disable agent mode if models are missing
                if self._agent_mode:
                    self._agent_mode = False
                    self.agentModeChanged.emit()
            
            self.agentModelsAvailableChanged.emit()
        else:
            self._models = []
            self._agent_models_available = False
            self._missing_agent_models = list(REQUIRED_AGENT_MODELS)
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
        
        # Clean up agent state
        if chat_id in self._agent_states:
            del self._agent_states[chat_id]
        if chat_id in self._pending_tool_calls:
            del self._pending_tool_calls[chat_id]
        
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
    
    @Slot(str, result=list)
    def getPendingToolCalls(self, chat_id: str) -> list:
        """Get pending tool calls for a chat that need user permission."""
        return self._pending_tool_calls.get(chat_id, [])
    
    @Slot(str, result=bool)
    def hasPendingToolCalls(self, chat_id: str) -> bool:
        """Check if a chat has pending tool calls awaiting permission."""
        calls = self._pending_tool_calls.get(chat_id, [])
        return any(tc.get("requires_permission", False) for tc in calls)
    
    @Slot(bool)
    def setAgentMode(self, enabled: bool) -> None:
        """Enable or disable agent mode."""
        if enabled and not self._agent_models_available:
            # Cannot enable agent mode without required models
            logger.warning(f"Cannot enable agent mode. Missing models: {self._missing_agent_models}")
            return
        self.agentMode = enabled
    
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
        
        # Use agent mode or regular chat
        if self._agent_mode:
            self._send_agent_message(chat_id, content, messages)
        else:
            self._send_regular_message(chat_id, messages)
    
    def _send_agent_message(self, chat_id: str, content: str, messages: list) -> None:
        """Send a message using the agent with tool calling."""
        # Store user message for later context during tool execution
        self._user_messages[chat_id] = content
        
        # Get agent state
        state = self._get_or_create_agent_state(chat_id)
        
        # Prepare history for agent
        history = [
            {"role": msg.role, "content": msg.content}
            for msg in messages[:-1]  # Exclude the message we just added
        ]
        
        # Create and start agent worker
        self._agent_worker = AgentWorker(
            agent_service=self._get_agent_service(),
            user_message=content,
            chat_id=chat_id,
            history=history,
            state=state,
        )
        self._agent_worker.response_ready.connect(self._on_agent_response_ready)
        self._agent_worker.response_error.connect(self._on_response_error)
        self._agent_worker.finished.connect(self._on_agent_worker_finished)
        self._agent_worker.start()
    
    def _send_regular_message(self, chat_id: str, messages: list) -> None:
        """Send a message using regular chat (no tools)."""
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
    
    def _on_agent_response_ready(self, chat_id: str, response: str, tool_calls: list) -> None:
        """Handle response from agent."""
        # Filter tool calls that need permission
        permission_required = [tc for tc in tool_calls if tc.get("requires_permission", False)]
        auto_approve = [tc for tc in tool_calls if not tc.get("requires_permission", False)]
        
        if permission_required:
            # Store pending tool calls and wait for user decision
            self._pending_tool_calls[chat_id] = tool_calls
            
            # Add partial response if any
            if response:
                self._db.add_message(chat_id, "assistant", response)
                self.messagesChanged.emit()
            
            # Emit signal to show permission UI
            self.toolCallsPending.emit(chat_id, permission_required)
            self.isLoading = False
            
        elif auto_approve:
            # Execute auto-approved tools immediately
            self._pending_tool_calls[chat_id] = tool_calls
            self._execute_tool_calls(chat_id, {tc["call_id"] for tc in auto_approve}, set())
        else:
            # No tool calls, just save the response
            self._finalize_response(chat_id, response)
    
    def _finalize_response(self, chat_id: str, response: str) -> None:
        """Finalize the agent response."""
        if response:
            self._db.add_message(chat_id, "assistant", response)
            self.messagesChanged.emit()
            self.chatsChanged.emit()
            self.responseReceived.emit(chat_id, response)
        
        # Clean up stored user message
        if chat_id in self._user_messages:
            del self._user_messages[chat_id]
        
        # Generate title for first message
        messages = self._db.get_messages(chat_id)
        if len(messages) == 2:
            user_message = messages[0].content
            if self._ollama.is_available() and self._current_model:
                self._start_title_generation(chat_id, user_message)
        
        self.isLoading = False
    
    @Slot(str, list, list)
    def respondToToolCalls(self, chat_id: str, approved_ids: list, denied_ids: list) -> None:
        """Respond to pending tool call permission requests."""
        approved_set = set(approved_ids)
        denied_set = set(denied_ids)
        
        self.isLoading = True
        self._execute_tool_calls(chat_id, approved_set, denied_set)
    
    def _execute_tool_calls(self, chat_id: str, approved_ids: set[str], denied_ids: set[str]) -> None:
        """Execute tool calls after user approval."""
        state = self._get_or_create_agent_state(chat_id)
        
        # Recreate pending tool calls from stored data
        pending = self._pending_tool_calls.get(chat_id, [])
        
        state.pending_tool_calls = []
        for tc in pending:
            permissions = [Permission(p) for p in tc.get("permissions", [])]
            state.pending_tool_calls.append(ToolCall(
                tool_name=tc["tool_name"],
                tool_description=tc["tool_description"],
                arguments=tc["arguments"],
                permissions=permissions,
                requires_permission=tc["requires_permission"],
                call_id=tc["call_id"],
            ))
        
        # Clear stored pending calls
        self._pending_tool_calls[chat_id] = []
        
        # Get stored user message and history for context
        user_message = self._user_messages.get(chat_id, "")
        messages = self._db.get_messages(chat_id)
        history = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        # Create and start tool execution worker
        self._tool_worker = ToolExecutionWorker(
            agent_service=self._get_agent_service(),
            chat_id=chat_id,
            state=state,
            approved_ids=approved_ids,
            denied_ids=denied_ids,
            user_message=user_message,
            history=history,
        )
        self._tool_worker.execution_complete.connect(self._on_tool_execution_complete)
        self._tool_worker.execution_error.connect(self._on_response_error)
        self._tool_worker.finished.connect(self._on_tool_worker_finished)
        self._tool_worker.start()
    
    def _on_tool_execution_complete(self, chat_id: str, response: str, new_tool_calls: list) -> None:
        """Handle tool execution completion."""
        # Check if there are new tool calls requiring permission
        permission_required = [tc for tc in new_tool_calls if tc.get("requires_permission", False)]
        auto_approve = [tc for tc in new_tool_calls if not tc.get("requires_permission", False)]
        
        if permission_required:
            # Store pending tool calls and wait for user decision
            self._pending_tool_calls[chat_id] = new_tool_calls
            
            # Add partial response if any
            if response:
                self._db.add_message(chat_id, "assistant", response)
                self.messagesChanged.emit()
            
            # Emit signal to show permission UI
            self.toolCallsPending.emit(chat_id, permission_required)
            self.isLoading = False
            
        elif auto_approve:
            # Execute auto-approved tools immediately
            self._pending_tool_calls[chat_id] = new_tool_calls
            self._execute_tool_calls(chat_id, {tc["call_id"] for tc in auto_approve}, set())
        else:
            # No more tool calls, finalize response
            self._finalize_response(chat_id, response)
    
    def _on_agent_worker_finished(self) -> None:
        """Clean up after agent worker finishes."""
        if self._agent_worker:
            self._agent_worker.deleteLater()
            self._agent_worker = None
    
    def _on_tool_worker_finished(self) -> None:
        """Clean up after tool worker finishes."""
        if self._tool_worker:
            self._tool_worker.deleteLater()
            self._tool_worker = None
    
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
