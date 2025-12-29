"""Pydantic models for tool arguments in the agent."""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


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
