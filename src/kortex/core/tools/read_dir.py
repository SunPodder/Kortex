"""Tool to read contents of a directory."""
from __future__ import annotations

import logging
from pathlib import Path

from kortex.core.tools.base import BaseTool, Permission, ToolResult

logger = logging.getLogger(__name__)


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
