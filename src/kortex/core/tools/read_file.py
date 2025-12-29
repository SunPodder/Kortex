"""Tool to read contents of a file."""
from __future__ import annotations

import logging
from pathlib import Path

from kortex.core.tools.base import BaseTool, Permission, ToolResult

logger = logging.getLogger(__name__)


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
