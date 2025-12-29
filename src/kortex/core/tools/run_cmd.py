"""Tool to execute shell commands."""
from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from typing import Optional

from kortex.core.tools.base import BaseTool, Permission, ToolResult

logger = logging.getLogger(__name__)


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
