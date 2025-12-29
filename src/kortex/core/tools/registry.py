"""Registry for managing available tools."""
from __future__ import annotations

import logging
from typing import Optional

from kortex.core.tools.base import BaseTool, ToolResult
from kortex.core.tools.read_dir import ReadDirectoryTool
from kortex.core.tools.read_file import ReadFileTool
from kortex.core.tools.write_file import WriteFileTool
from kortex.core.tools.run_cmd import RunCommandTool

logger = logging.getLogger(__name__)


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
