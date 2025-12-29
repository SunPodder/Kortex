"""Tool to write content to a file."""
from __future__ import annotations

import logging
from pathlib import Path

from kortex.core.tools.base import BaseTool, Permission, ToolResult

logger = logging.getLogger(__name__)


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
