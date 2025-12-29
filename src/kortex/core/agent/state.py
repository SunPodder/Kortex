"""Agent state management."""
from __future__ import annotations

from dataclasses import dataclass, field

from kortex.core.tools import ToolCall, ToolResult


@dataclass
class AgentState:
    """State for an agent conversation."""
    messages: list = field(default_factory=list)
    pending_tool_calls: list[ToolCall] = field(default_factory=list)
    completed_tool_calls: dict[str, ToolResult] = field(default_factory=dict)
    denied_tool_calls: set[str] = field(default_factory=set)
    is_waiting_for_permission: bool = False
    current_response: str = ""
    # Track tool execution context for multi-step tool calls
    tool_execution_context: list[dict] = field(default_factory=list)
    # Track if we're in the middle of a tool chain
    in_tool_chain: bool = False
