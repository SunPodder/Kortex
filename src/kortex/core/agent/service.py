"""Agent service for agentic AI capabilities with tool calling.

This module implements a router-based agent system that uses:
- gemma3:270m as a router model to decide if tools are needed
- functiongemma:270m for actual tool calling
- The user's selected model for non-tool responses and summarization
"""
from __future__ import annotations

import logging
import uuid
from typing import Optional

from langchain_ollama import ChatOllama
from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.tools import StructuredTool

from kortex.core.tools import ToolCall, tool_registry
from kortex.core.agent.state import AgentState
from kortex.core.agent.models import (
    ReadDirArgs,
    ReadFileArgs,
    WriteFileArgs,
    RunCmdArgs,
)
from kortex.core.agent.constants import (
    ROUTER_MODEL,
    TOOL_MODEL,
    ROUTER_PROMPT,
    TOOL_PROMPT,
    SUMMARY_PROMPT,
)

logger = logging.getLogger(__name__)


class AgentService:
    """Service for running an AI agent with tool capabilities.
    
    This service implements a router-based approach:
    1. Uses gemma3:270m as a router to determine if tools are needed
    2. Routes to functiongemma:270m for tool calls
    3. Uses the user's selected model for non-tool responses and summarization
    """
    
    # Prompts from constants
    ROUTER_PROMPT = ROUTER_PROMPT
    TOOL_PROMPT = TOOL_PROMPT
    SUMMARY_PROMPT = SUMMARY_PROMPT

    def __init__(
        self,
        model_name: str = "llama3.2",
        host: str = "http://localhost:11434",
    ) -> None:
        self.model_name = model_name  # User's selected model
        self.host = host
        self._router_llm: Optional[ChatOllama] = None
        self._tool_llm: Optional[ChatOllama] = None
        self._chat_llm: Optional[ChatOllama] = None
        self._langchain_tools: list[StructuredTool] = []
        self._init_llms()
    
    def _init_llms(self) -> None:
        """Initialize the LangChain LLMs for routing, tools, and chat."""
        try:
            # Create LangChain tools from our tool registry
            self._langchain_tools = self._create_langchain_tools()
            
            # Router LLM (gemma3:270m) - for deciding if tools are needed
            self._router_llm = ChatOllama(
                model=ROUTER_MODEL,
                base_url=self.host,
            )
            
            # Tool LLM (functiongemma:270m) - for actual tool calling
            self._tool_llm = ChatOllama(
                model=TOOL_MODEL,
                base_url=self.host,
            )
            
            # Bind tools to the tool LLM
            if self._langchain_tools:
                self._tool_llm = self._tool_llm.bind_tools(self._langchain_tools)
            
            # Chat LLM (user's selected model) - for non-tool responses and summarization
            self._chat_llm = ChatOllama(
                model=self.model_name,
                base_url=self.host,
            )
            
            logger.info(f"Initialized agent with router={ROUTER_MODEL}, tools={TOOL_MODEL}, chat={self.model_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize agent LLMs: {e}")
            self._router_llm = None
            self._tool_llm = None
            self._chat_llm = None
    
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
        """Update the user's selected model (for chat and summarization)."""
        if model_name != self.model_name:
            self.model_name = model_name
            # Only reinitialize the chat LLM, not the router or tool LLMs
            try:
                self._chat_llm = ChatOllama(
                    model=self.model_name,
                    base_url=self.host,
                )
                logger.info(f"Updated chat model to {self.model_name}")
            except Exception as e:
                logger.error(f"Failed to update chat model: {e}")
    
    def create_state(self) -> AgentState:
        """Create a new agent state."""
        return AgentState()
    
    def _route_message(self, user_message: str, history: list[dict] = None) -> bool:
        """Use the router model to determine if tools are needed.
        
        Returns:
            True if tools are needed, False for regular chat
        """
        if not self._router_llm:
            logger.warning("Router LLM not available, defaulting to chat")
            return False
        
        try:
            messages = [
                SystemMessage(content=self.ROUTER_PROMPT),
                HumanMessage(content=user_message),
            ]
            
            response = self._router_llm.invoke(messages)
            decision = response.content.strip().upper() if hasattr(response, 'content') else ""
            
            logger.info(f"Router decision for '{user_message[:50]}...': {decision}")
            
            return "TOOLS" in decision
            
        except Exception as e:
            logger.error(f"Router error: {e}, defaulting to chat")
            return False
    
    def _chat_response(
        self,
        user_message: str,
        history: list[dict] = None,
    ) -> str:
        """Get a regular chat response using the user's selected model."""
        if not self._chat_llm:
            return "Error: Chat model not initialized."
        
        try:
            messages = []
            
            # Add conversation history
            if history:
                for msg in history:
                    if msg["role"] == "user":
                        messages.append(HumanMessage(content=msg["content"]))
                    elif msg["role"] == "assistant":
                        messages.append(AIMessage(content=msg["content"]))
            
            # Add the new user message
            messages.append(HumanMessage(content=user_message))
            
            response = self._chat_llm.invoke(messages)
            return response.content if hasattr(response, 'content') else str(response)
            
        except Exception as e:
            logger.error(f"Chat response error: {e}")
            return f"Error: {str(e)}"
    
    def _summarize_tool_results(
        self,
        user_message: str,
        tool_context: list[dict],
        history: list[dict] = None,
    ) -> str:
        """Summarize tool execution results using the user's selected model."""
        if not self._chat_llm:
            return "Error: Chat model not initialized."
        
        try:
            # Build context about what tools were executed
            tool_summary = "Tool execution results:\n"
            for ctx in tool_context:
                tool_name = ctx.get("tool_name", "unknown")
                args = ctx.get("arguments", {})
                result = ctx.get("result", {})
                success = result.get("success", False)
                output = result.get("output", "")
                error = result.get("error", "")
                
                tool_summary += f"\n- {tool_name}({args}):\n"
                if success:
                    tool_summary += f"  Success: {output[:500]}...\n" if len(output) > 500 else f"  Success: {output}\n"
                else:
                    tool_summary += f"  Failed: {error}\n"
            
            messages = [
                SystemMessage(content=self.SUMMARY_PROMPT),
            ]
            
            # Add relevant history
            if history:
                for msg in history[-4:]:  # Last few messages for context
                    if msg["role"] == "user":
                        messages.append(HumanMessage(content=msg["content"]))
                    elif msg["role"] == "assistant":
                        messages.append(AIMessage(content=msg["content"]))
            
            # Add the context
            messages.append(HumanMessage(
                content=f"User request: {user_message}\n\n{tool_summary}\n\nPlease provide a helpful response based on these results."
            ))
            
            response = self._chat_llm.invoke(messages)
            return response.content if hasattr(response, 'content') else str(response)
            
        except Exception as e:
            logger.error(f"Summarization error: {e}")
            return f"Tools executed but summarization failed: {str(e)}"
    
    def process_message(
        self,
        user_message: str,
        state: AgentState,
        history: list[dict] = None,
    ) -> tuple[str, list[ToolCall], AgentState]:
        """
        Process a user message using the router-based approach.
        
        1. Router (gemma3:270m) decides if tools are needed
        2. If tools needed: functiongemma handles tool calls
        3. If no tools: user's selected model handles the response
        
        Returns:
            tuple of (response_text, pending_tool_calls, updated_state)
        """
        if not self._router_llm or not self._tool_llm or not self._chat_llm:
            return "Error: Agent not initialized. Please check if Ollama is running and required models are available.", [], state
        
        try:
            # Step 1: Route the message
            needs_tools = self._route_message(user_message, history)
            
            if not needs_tools:
                # Step 2a: Use chat model for regular response
                logger.info("Router decided: CHAT - using selected model")
                response = self._chat_response(user_message, history)
                state.current_response = response
                return response, [], state
            
            # Step 2b: Use tool model for tool calling
            logger.info("Router decided: TOOLS - using functiongemma")
            return self._process_tool_message(user_message, state, history)
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return f"Error: {str(e)}", [], state
    
    def _process_tool_message(
        self,
        user_message: str,
        state: AgentState,
        history: list[dict] = None,
    ) -> tuple[str, list[ToolCall], AgentState]:
        """Process a message that requires tools using functiongemma."""
        try:
            # Build messages list for tool model
            messages = [SystemMessage(content=self.TOOL_PROMPT)]
            
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
            state.in_tool_chain = True
            
            # Get response from tool LLM (functiongemma)
            response = self._tool_llm.invoke(messages)
            
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
            
            # Get text response (might be empty if only tool calls)
            response_text = response.content if hasattr(response, 'content') else ""
            state.current_response = response_text
            
            return response_text, pending_calls, state
            
        except Exception as e:
            logger.error(f"Error processing tool message: {e}")
            return f"Error: {str(e)}", [], state
    
    def execute_tool_calls(
        self,
        state: AgentState,
        approved_call_ids: set[str] = None,
        denied_call_ids: set[str] = None,
        user_message: str = "",
        history: list[dict] = None,
    ) -> tuple[str, list[ToolCall], AgentState]:
        """
        Execute approved tool calls and continue the conversation.
        
        Uses functiongemma for tool execution, then summarizes with selected model.
        
        Returns:
            tuple of (response_text, new_pending_tool_calls, updated_state)
        """
        if not self._tool_llm or not self._chat_llm:
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
                from kortex.core.tools import ToolResult
                result = ToolResult(
                    success=False,
                    output="",
                    error="User denied permission for this tool call.",
                )
                tool_results.append({
                    "call_id": call_id,
                    "tool_name": tool_call.tool_name,
                    "arguments": tool_call.arguments,
                    "result": result.to_dict(),
                })
                # Add to context for summarization
                state.tool_execution_context.append({
                    "tool_name": tool_call.tool_name,
                    "arguments": tool_call.arguments,
                    "result": result.to_dict(),
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
                    "arguments": tool_call.arguments,
                    "result": result.to_dict(),
                })
                # Add to context for summarization
                state.tool_execution_context.append({
                    "tool_name": tool_call.tool_name,
                    "arguments": tool_call.arguments,
                    "result": result.to_dict(),
                })
                logger.info(f"Executed tool {tool_call.tool_name}: success={result.success}")
        
        # Clear pending calls
        state.pending_tool_calls = []
        state.is_waiting_for_permission = False
        
        # If there were tool results, check if more tools are needed
        if tool_results:
            return self._continue_with_tool_results(state, tool_results, user_message, history)
        
        return state.current_response, [], state
    
    def _continue_with_tool_results(
        self,
        state: AgentState,
        tool_results: list[dict],
        user_message: str = "",
        history: list[dict] = None,
    ) -> tuple[str, list[ToolCall], AgentState]:
        """Continue the conversation after tool execution.
        
        Uses functiongemma to determine if more tools are needed.
        If no more tools, summarizes with the selected model.
        """
        try:
            # Rebuild messages with tool results for functiongemma
            messages = state.messages.copy()
            
            # Add an AI message with tool calls (reconstructed)
            tool_calls_for_message = []
            for tr in tool_results:
                tool_calls_for_message.append({
                    "name": tr["tool_name"],
                    "args": tr["arguments"],
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
                if result["success"]:
                    content = result["output"]
                else:
                    content = f"Error: {result['error']}"
                
                tool_msg = ToolMessage(
                    content=content,
                    tool_call_id=tr["call_id"],
                )
                messages.append(tool_msg)
            
            # Get next response from tool LLM (functiongemma) to check for more tool calls
            response = self._tool_llm.invoke(messages)
            
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
                        logger.info(f"Additional tool call requested: {tool_name}")
            
            state.messages = messages
            state.pending_tool_calls = pending_calls
            state.is_waiting_for_permission = any(tc.requires_permission for tc in pending_calls)
            
            response_text = response.content if hasattr(response, 'content') else ""
            state.current_response = response_text
            
            # If there are more tool calls, return them for execution
            if pending_calls:
                # Auto-execute non-permission-requiring tools
                auto_approve_calls = [tc for tc in pending_calls if not tc.requires_permission]
                if auto_approve_calls and not state.is_waiting_for_permission:
                    auto_ids = {tc.call_id for tc in auto_approve_calls}
                    return self.execute_tool_calls(
                        state,
                        approved_call_ids=auto_ids,
                        user_message=user_message,
                        history=history,
                    )
                
                # Return pending calls that need permission
                return response_text, pending_calls, state
            
            # No more tool calls - summarize with selected model
            state.in_tool_chain = False
            
            if state.tool_execution_context:
                # Summarize all tool results with the user's selected model
                summary = self._summarize_tool_results(
                    user_message or state.messages[1].content if len(state.messages) > 1 else "",
                    state.tool_execution_context,
                    history,
                )
                state.current_response = summary
                # Clear the tool context after summarization
                state.tool_execution_context = []
                return summary, [], state
            
            return response_text, [], state
            
        except Exception as e:
            logger.error(f"Error continuing conversation: {e}")
            # Try to summarize what we have
            if state.tool_execution_context:
                summary = self._summarize_tool_results(
                    user_message or "",
                    state.tool_execution_context,
                    history,
                )
                state.tool_execution_context = []
                return summary, [], state
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
