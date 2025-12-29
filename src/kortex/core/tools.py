"""Tool definitions with permission system for agentic capabilities."""
from __future__ import annotations

import logging
import os
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional

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


class ReadDirectoryTool(BaseTool):
    """Tool to list contents of a directory."""
    
    name = "read_dir"
    description = "List all files and subdirectories in a given directory path. Returns a list of file/folder names with their types."
    permissions = [Permission.FS_READ]
    
    def get_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The absolute or relative path to the directory to list",
                },
                "show_hidden": {
                    "type": "boolean",
                    "description": "Whether to include hidden files (starting with .)",
                    "default": False,
                },
            },
            "required": ["path"],
        }
    
    def execute(self, path: str, show_hidden: bool = False) -> ToolResult:
        """List directory contents."""
        try:
            target_path = Path(path).expanduser().resolve()
            
            if not target_path.exists():
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Directory does not exist: {path}",
                )
            
            if not target_path.is_dir():
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Path is not a directory: {path}",
                )
            
            entries = []
            for entry in sorted(target_path.iterdir()):
                if not show_hidden and entry.name.startswith("."):
                    continue
                
                entry_type = "dir" if entry.is_dir() else "file"
                size = ""
                if entry.is_file():
                    size = f" ({entry.stat().st_size} bytes)"
                
                entries.append(f"[{entry_type}] {entry.name}{size}")
            
            if not entries:
                output = f"Directory '{path}' is empty."
            else:
                output = f"Contents of '{path}':\n" + "\n".join(entries)
            
            return ToolResult(success=True, output=output)
            
        except PermissionError:
            return ToolResult(
                success=False,
                output="",
                error=f"Permission denied accessing: {path}",
            )
        except Exception as e:
            logger.error(f"Error reading directory {path}: {e}")
            return ToolResult(
                success=False,
                output="",
                error=str(e),
            )


class ReadFileTool(BaseTool):
    """Tool to read contents of a file."""
    
    name = "read_file"
    description = "Read and return the contents of a text file. Useful for viewing source code, configuration files, documents, etc."
    permissions = [Permission.FS_READ]
    
    def get_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The absolute or relative path to the file to read",
                },
                "max_lines": {
                    "type": "integer",
                    "description": "Maximum number of lines to read (default: 500)",
                    "default": 500,
                },
            },
            "required": ["path"],
        }
    
    def execute(self, path: str, max_lines: int = 500) -> ToolResult:
        """Read file contents."""
        try:
            target_path = Path(path).expanduser().resolve()
            
            if not target_path.exists():
                return ToolResult(
                    success=False,
                    output="",
                    error=f"File does not exist: {path}",
                )
            
            if not target_path.is_file():
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Path is not a file: {path}",
                )
            
            # Check file size first
            file_size = target_path.stat().st_size
            if file_size > 1_000_000:  # 1MB limit
                return ToolResult(
                    success=False,
                    output="",
                    error=f"File too large ({file_size} bytes). Maximum size is 1MB.",
                )
            
            # Try to read as text
            try:
                with open(target_path, "r", encoding="utf-8") as f:
                    lines = []
                    for i, line in enumerate(f):
                        if i >= max_lines:
                            lines.append(f"\n... (truncated, showing first {max_lines} lines)")
                            break
                        lines.append(line.rstrip())
                    
                    content = "\n".join(lines)
                    output = f"Contents of '{path}':\n```\n{content}\n```"
                    return ToolResult(success=True, output=output)
                    
            except UnicodeDecodeError:
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Cannot read file as text (binary file?): {path}",
                )
            
        except PermissionError:
            return ToolResult(
                success=False,
                output="",
                error=f"Permission denied reading: {path}",
            )
        except Exception as e:
            logger.error(f"Error reading file {path}: {e}")
            return ToolResult(
                success=False,
                output="",
                error=str(e),
            )


class WriteFileTool(BaseTool):
    """Tool to write content to a file."""
    
    name = "write_file"
    description = "Write or create a file with the given content. Can create new files or overwrite existing ones. Use with caution."
    permissions = [Permission.FS_WRITE]
    
    def get_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The absolute or relative path to the file to write",
                },
                "content": {
                    "type": "string",
                    "description": "The content to write to the file",
                },
                "append": {
                    "type": "boolean",
                    "description": "If true, append to file instead of overwriting",
                    "default": False,
                },
            },
            "required": ["path", "content"],
        }
    
    def execute(self, path: str, content: str, append: bool = False) -> ToolResult:
        """Write content to a file."""
        try:
            target_path = Path(path).expanduser().resolve()
            
            # Create parent directories if needed
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            mode = "a" if append else "w"
            action = "Appended to" if append else "Wrote to"
            
            with open(target_path, mode, encoding="utf-8") as f:
                f.write(content)
            
            return ToolResult(
                success=True,
                output=f"{action} file: {path} ({len(content)} characters)",
            )
            
        except PermissionError:
            return ToolResult(
                success=False,
                output="",
                error=f"Permission denied writing to: {path}",
            )
        except Exception as e:
            logger.error(f"Error writing file {path}: {e}")
            return ToolResult(
                success=False,
                output="",
                error=str(e),
            )


class RunCommandTool(BaseTool):
    """Tool to execute shell commands."""
    
    name = "run_cmd"
    description = "Execute a shell command and return its output. Use for running scripts, installing packages, or system operations. Be careful with destructive commands."
    permissions = [Permission.RUN_CMD]
    
    def get_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The shell command to execute",
                },
                "working_dir": {
                    "type": "string",
                    "description": "The working directory for the command (optional)",
                },
                "timeout": {
                    "type": "integer",
                    "description": "Timeout in seconds (default: 30)",
                    "default": 30,
                },
            },
            "required": ["command"],
        }
    
    def execute(
        self,
        command: str,
        working_dir: Optional[str] = None,
        timeout: int = 30,
    ) -> ToolResult:
        """Execute a shell command."""
        try:
            cwd = None
            if working_dir:
                cwd = Path(working_dir).expanduser().resolve()
                if not cwd.exists():
                    return ToolResult(
                        success=False,
                        output="",
                        error=f"Working directory does not exist: {working_dir}",
                    )
            
            # Run the command
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            
            output_parts = []
            if result.stdout:
                output_parts.append(f"stdout:\n{result.stdout}")
            if result.stderr:
                output_parts.append(f"stderr:\n{result.stderr}")
            
            output = "\n".join(output_parts) if output_parts else "(no output)"
            
            if result.returncode != 0:
                return ToolResult(
                    success=False,
                    output=output,
                    error=f"Command exited with code {result.returncode}",
                )
            
            return ToolResult(
                success=True,
                output=f"Command executed successfully:\n{output}",
            )
            
        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                output="",
                error=f"Command timed out after {timeout} seconds",
            )
        except Exception as e:
            logger.error(f"Error executing command '{command}': {e}")
            return ToolResult(
                success=False,
                output="",
                error=str(e),
            )


class ToolRegistry:
    """Registry for managing available tools."""
    
    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}
        self._register_default_tools()
    
    def _register_default_tools(self) -> None:
        """Register the default set of tools."""
        self.register(ReadDirectoryTool())
        self.register(ReadFileTool())
        self.register(WriteFileTool())
        self.register(RunCommandTool())
    
    def register(self, tool: BaseTool) -> None:
        """Register a tool."""
        self._tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")
    
    def get(self, name: str) -> Optional[BaseTool]:
        """Get a tool by name."""
        return self._tools.get(name)
    
    def get_all(self) -> list[BaseTool]:
        """Get all registered tools."""
        return list(self._tools.values())
    
    def get_tool_schemas(self) -> list[dict]:
        """Get schemas for all tools in OpenAI function format."""
        schemas = []
        for tool in self._tools.values():
            schemas.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.get_schema(),
                },
            })
        return schemas
    
    def execute_tool(self, name: str, arguments: dict) -> ToolResult:
        """Execute a tool by name with given arguments."""
        tool = self.get(name)
        if not tool:
            return ToolResult(
                success=False,
                output="",
                error=f"Unknown tool: {name}",
            )
        
        try:
            return tool.execute(**arguments)
        except TypeError as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Invalid arguments for tool {name}: {e}",
            )


# Global tool registry instance
tool_registry = ToolRegistry()
