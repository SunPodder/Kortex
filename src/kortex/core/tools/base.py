"""Base classes and types for tools with permission system."""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class Permission(Enum):
    """Permission types for tools."""
    FS_READ = "fs_read"      # Read files/directories
    FS_WRITE = "fs_write"    # Write/modify files
    INTERNET = "internet"    # Network access
    RUN_CMD = "run_cmd"      # Execute shell commands
    
    @property
    def requires_explicit_permission(self) -> bool:
        """Check if this permission requires explicit user approval."""
        return self in {
            Permission.FS_WRITE,
            Permission.INTERNET,
            Permission.RUN_CMD,
        }
    
    @property
    def display_name(self) -> str:
        """Human-readable name for the permission."""
        names = {
            Permission.FS_READ: "Read Files",
            Permission.FS_WRITE: "Write Files",
            Permission.INTERNET: "Internet Access",
            Permission.RUN_CMD: "Run Commands",
        }
        return names.get(self, self.value)
    
    @property
    def description(self) -> str:
        """Description of what this permission allows."""
        descriptions = {
            Permission.FS_READ: "Read files and directories from your system",
            Permission.FS_WRITE: "Create or modify files on your system",
            Permission.INTERNET: "Access the internet to fetch data",
            Permission.RUN_CMD: "Execute shell commands on your system",
        }
        return descriptions.get(self, "Unknown permission")


@dataclass
class ToolResult:
    """Result from a tool execution."""
    success: bool
    output: str
    error: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "output": self.output,
            "error": self.error,
        }


@dataclass
class ToolCall:
    """Represents a pending tool call that may need permission."""
    tool_name: str
    tool_description: str
    arguments: dict[str, Any]
    permissions: list[Permission]
    requires_permission: bool
    call_id: str = ""
    
    def to_dict(self) -> dict:
        return {
            "tool_name": self.tool_name,
            "tool_description": self.tool_description,
            "arguments": self.arguments,
            "permissions": [p.value for p in self.permissions],
            "permission_names": [p.display_name for p in self.permissions],
            "permission_descriptions": [p.description for p in self.permissions],
            "requires_permission": self.requires_permission,
            "call_id": self.call_id,
        }


class BaseTool(ABC):
    """Base class for all tools."""
    
    name: str
    description: str
    permissions: list[Permission]
    
    @property
    def requires_explicit_permission(self) -> bool:
        """Check if any permission requires explicit approval."""
        return any(p.requires_explicit_permission for p in self.permissions)
    
    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given arguments."""
        pass
    
    @abstractmethod
    def get_schema(self) -> dict:
        """Get the JSON schema for tool arguments."""
        pass
    
    def create_tool_call(self, arguments: dict, call_id: str = "") -> ToolCall:
        """Create a ToolCall object for this tool."""
        return ToolCall(
            tool_name=self.name,
            tool_description=self.description,
            arguments=arguments,
            permissions=self.permissions,
            requires_permission=self.requires_explicit_permission,
            call_id=call_id,
        )
