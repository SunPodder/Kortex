"""Agent service for agentic AI capabilities with tool calling."""
from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass, field
from typing import Any, Generator, Optional

from langchain_ollama import ChatOllama
from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from kortex.core.tools import (
    BaseTool,
    Permission,
    ToolCall,
    ToolResult,
    tool_registry,
)

logger = logging.getLogger(__name__)


# Pydantic models for tool arguments
class ReadDirArgs(BaseModel):
    """Arguments for read_dir tool."""
    path: str = Field(description="The absolute or relative path to the directory to list")
    show_hidden: bool = Field(default=False, description="Whether to include hidden files")


class ReadFileArgs(BaseModel):
    """Arguments for read_file tool."""
    path: str = Field(description="The absolute or relative path to the file to read")
    max_lines: int = Field(default=500, description="Maximum number of lines to read")


class WriteFileArgs(BaseModel):
    """Arguments for write_file tool."""
    path: str = Field(description="The absolute or relative path to the file to write")
    content: str = Field(description="The content to write to the file")
    append: bool = Field(default=False, description="If true, append to file instead of overwriting")


class RunCmdArgs(BaseModel):
    """Arguments for run_cmd tool."""
    command: str = Field(description="The shell command to execute")
    working_dir: Optional[str] = Field(default=None, description="The working directory for the command")
    timeout: int = Field(default=30, description="Timeout in seconds")


@dataclass
class AgentState:
    """State for an agent conversation."""
    messages: list = field(default_factory=list)
    pending_tool_calls: list[ToolCall] = field(default_factory=list)
    completed_tool_calls: dict[str, ToolResult] = field(default_factory=dict)
    denied_tool_calls: set[str] = field(default_factory=set)
    is_waiting_for_permission: bool = False
    current_response: str = ""
    

class AgentService:
    """Service for running an AI agent with tool capabilities."""
    
    # System prompt for the agent
    SYSTEM_PROMPT = """You are a helpful AI assistant with access to tools that allow you to interact with the user's computer.

Available tools:
- read_dir: List contents of a directory
- read_file: Read contents of a text file
- write_file: Write or create a file with content
- run_cmd: Execute shell commands

When using tools:
1. Think step by step about what you need to do
2. Use tools when they would help accomplish the user's request
3. You can chain multiple tool calls to accomplish complex tasks
4. Always explain what you're doing and why
5. If a tool call fails or is denied, explain the situation and offer alternatives

Important:
- Be careful with write_file and run_cmd as they can modify the system
- Always confirm destructive operations with clear explanations
- If you need to perform multiple steps, do them one at a time and verify each step"""

    def __init__(self, model_name: str = "llama3.2", host: str = "http://localhost:11434") -> None:
        self.model_name = model_name
        self.host = host
        self._llm: Optional[ChatOllama] = None
        self._langchain_tools: list[StructuredTool] = []
        self._init_llm()
    
    def _init_llm(self) -> None:
        """Initialize the LangChain LLM with tools."""
        try:
            # Create LangChain tools from our tool registry
            self._langchain_tools = self._create_langchain_tools()
            
            # Create the LLM
            self._llm = ChatOllama(
                model=self.model_name,
                base_url=self.host,
            )
            
            # Bind tools to the LLM
            if self._langchain_tools:
                self._llm = self._llm.bind_tools(self._langchain_tools)
            
            logger.info(f"Initialized agent with model {self.model_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize agent LLM: {e}")
            self._llm = None
    
    def _create_langchain_tools(self) -> list[StructuredTool]:
        """Create LangChain StructuredTool objects from our tools."""
        tools = []
        
        # Map tool names to their Pydantic arg schemas
        arg_schemas = {
            "read_dir": ReadDirArgs,
            "read_file": ReadFileArgs,
            "write_file": WriteFileArgs,
            "run_cmd": RunCmdArgs,
        }
        
        for base_tool in tool_registry.get_all():
            if base_tool.name in arg_schemas:
                # Create a wrapper function that we won't actually use
                # (we handle tool execution separately)
                def dummy_func(**kwargs):
                    return "Tool execution handled externally"
                
                tool = StructuredTool(
                    name=base_tool.name,
                    description=base_tool.description,
                    args_schema=arg_schemas[base_tool.name],
                    func=dummy_func,
                )
                tools.append(tool)
        
        return tools
    
    def update_model(self, model_name: str) -> None:
        """Update the model being used."""
        if model_name != self.model_name:
            self.model_name = model_name
            self._init_llm()
    
    def create_state(self) -> AgentState:
        """Create a new agent state."""
        return AgentState()
    
    def process_message(
        self,
        user_message: str,
        state: AgentState,
        history: list[dict] = None,
    ) -> tuple[str, list[ToolCall], AgentState]:
        """
        Process a user message and return the response with any pending tool calls.
        
        Returns:
            tuple of (response_text, pending_tool_calls, updated_state)
        """
        if not self._llm:
            return "Error: Agent not initialized. Please check if Ollama is running.", [], state
        
        try:
            # Build messages list
            messages = [SystemMessage(content=self.SYSTEM_PROMPT)]
            
            # Add conversation history
            if history:
                for msg in history:
                    if msg["role"] == "user":
                        messages.append(HumanMessage(content=msg["content"]))
                    elif msg["role"] == "assistant":
                        messages.append(AIMessage(content=msg["content"]))
            
            # Add the new user message
            messages.append(HumanMessage(content=user_message))
            
            # Store in state
            state.messages = messages
            
            # Get response from LLM
            response = self._llm.invoke(messages)
            
            # Check for tool calls
            pending_calls = []
            if hasattr(response, 'tool_calls') and response.tool_calls:
                for tc in response.tool_calls:
                    tool_name = tc["name"]
                    arguments = tc["args"]
                    call_id = tc.get("id", str(uuid.uuid4()))
                    
                    # Get the tool and create a ToolCall
                    tool = tool_registry.get(tool_name)
                    if tool:
                        tool_call = tool.create_tool_call(arguments, call_id)
                        pending_calls.append(tool_call)
                        logger.info(f"Tool call requested: {tool_name} with args {arguments}")
            
            state.pending_tool_calls = pending_calls
            state.is_waiting_for_permission = any(tc.requires_permission for tc in pending_calls)
            
            # Get text response
            response_text = response.content if hasattr(response, 'content') else str(response)
            state.current_response = response_text
            
            return response_text, pending_calls, state
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return f"Error: {str(e)}", [], state
    
    def execute_tool_calls(
        self,
        state: AgentState,
        approved_call_ids: set[str] = None,
        denied_call_ids: set[str] = None,
    ) -> tuple[str, list[ToolCall], AgentState]:
        """
        Execute approved tool calls and continue the conversation.
        
        Returns:
            tuple of (response_text, new_pending_tool_calls, updated_state)
        """
        if not self._llm:
            return "Error: Agent not initialized.", [], state
        
        approved_call_ids = approved_call_ids or set()
        denied_call_ids = denied_call_ids or set()
        
        # Add denied calls to state
        state.denied_tool_calls.update(denied_call_ids)
        
        # Execute approved tool calls
        tool_results = []
        for tool_call in state.pending_tool_calls:
            call_id = tool_call.call_id
            
            if call_id in denied_call_ids:
                # User denied this tool call
                tool_results.append({
                    "call_id": call_id,
                    "tool_name": tool_call.tool_name,
                    "result": ToolResult(
                        success=False,
                        output="",
                        error="User denied permission for this tool call.",
                    ),
                })
            elif call_id in approved_call_ids or not tool_call.requires_permission:
                # Execute the tool
                result = tool_registry.execute_tool(
                    tool_call.tool_name,
                    tool_call.arguments,
                )
                state.completed_tool_calls[call_id] = result
                tool_results.append({
                    "call_id": call_id,
                    "tool_name": tool_call.tool_name,
                    "result": result,
                })
                logger.info(f"Executed tool {tool_call.tool_name}: success={result.success}")
        
        # Clear pending calls
        state.pending_tool_calls = []
        state.is_waiting_for_permission = False
        
        # If there were tool results, continue the conversation
        if tool_results:
            return self._continue_with_tool_results(state, tool_results)
        
        return state.current_response, [], state
    
    def _continue_with_tool_results(
        self,
        state: AgentState,
        tool_results: list[dict],
    ) -> tuple[str, list[ToolCall], AgentState]:
        """Continue the conversation after tool execution."""
        try:
            # Rebuild messages with tool results
            messages = state.messages.copy()
            
            # Add an AI message with tool calls (reconstructed)
            tool_calls_for_message = []
            for tr in tool_results:
                tool_calls_for_message.append({
                    "name": tr["tool_name"],
                    "args": {},  # Args already used
                    "id": tr["call_id"],
                })
            
            # Add AI message that requested tools
            ai_msg = AIMessage(
                content=state.current_response or "",
                tool_calls=tool_calls_for_message,
            )
            messages.append(ai_msg)
            
            # Add tool result messages
            for tr in tool_results:
                result = tr["result"]
                if result.success:
                    content = result.output
                else:
                    content = f"Error: {result.error}"
                
                tool_msg = ToolMessage(
                    content=content,
                    tool_call_id=tr["call_id"],
                )
                messages.append(tool_msg)
            
            # Get next response from LLM
            response = self._llm.invoke(messages)
            
            # Check for more tool calls
            pending_calls = []
            if hasattr(response, 'tool_calls') and response.tool_calls:
                for tc in response.tool_calls:
                    tool_name = tc["name"]
                    arguments = tc["args"]
                    call_id = tc.get("id", str(uuid.uuid4()))
                    
                    tool = tool_registry.get(tool_name)
                    if tool:
                        tool_call = tool.create_tool_call(arguments, call_id)
                        pending_calls.append(tool_call)
            
            state.messages = messages
            state.pending_tool_calls = pending_calls
            state.is_waiting_for_permission = any(tc.requires_permission for tc in pending_calls)
            
            response_text = response.content if hasattr(response, 'content') else str(response)
            state.current_response = response_text
            
            # If there are auto-approvable tool calls, execute them immediately
            auto_approve_calls = [tc for tc in pending_calls if not tc.requires_permission]
            if auto_approve_calls and not state.is_waiting_for_permission:
                auto_ids = {tc.call_id for tc in auto_approve_calls}
                return self.execute_tool_calls(state, approved_call_ids=auto_ids)
            
            return response_text, pending_calls, state
            
        except Exception as e:
            logger.error(f"Error continuing conversation: {e}")
            return f"Error: {str(e)}", [], state


# Global agent service instance (will be initialized with model name)
_agent_service: Optional[AgentService] = None


def get_agent_service(model_name: str = "llama3.2", host: str = "http://localhost:11434") -> AgentService:
    """Get or create the global agent service."""
    global _agent_service
    
    if _agent_service is None:
        _agent_service = AgentService(model_name=model_name, host=host)
    elif _agent_service.model_name != model_name:
        _agent_service.update_model(model_name)
    
    return _agent_service
