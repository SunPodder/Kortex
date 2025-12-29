"""Utility functions for the agent module."""
from __future__ import annotations


def check_required_models(ollama_models: list[str]) -> tuple[bool, list[str]]:
    """Check if required models for agent mode are available.
    
    Args:
        ollama_models: List of model names available in Ollama
        
    Returns:
        Tuple of (all_available, missing_models)
    """
    from kortex.core.agent.constants import REQUIRED_AGENT_MODELS
    
    missing = []
    for required in REQUIRED_AGENT_MODELS:
        # Check if the model name matches (ignoring version tags)
        found = False
        for available in ollama_models:
            # Match base name (e.g., "gemma3:270m" matches "gemma3:270m")
            if available == required or available.startswith(required.split(":")[0] + ":"):
                # More precise check
                if available == required:
                    found = True
                    break
        if not found:
            missing.append(required)
    
    return len(missing) == 0, missing
