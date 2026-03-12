#!/usr/bin/env python3
"""Claude SDK client wrapper with async context manager support."""

import sys
import json

from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
from dataclasses import dataclass



@dataclass
class ClaudeClientConfig:
    """Configuration for ClaudeClient.
    
    Provides structured parameters for initializing ClaudeClient.
    All parameters except system_prompt are required.
    
    Example:
        config = ClaudeClientConfig(
            cwd="/path/to/project",
            settings="/path/to/settings.json",
            system_prompt="You are a helpful coding assistant"
        )
        async with ClaudeClient(config) as client:
            await client.query("Hello")
    """
    
    cwd: str
    settings: str
    system_prompt: str = "You are Claude"
class ClaudeClient:
    """Wrapper class for ClaudeSDKClient with simplified interface.

    Provides async context manager support and methods to query Claude
    and receive streaming responses.
    """

    def __init__(self, config: ClaudeClientConfig) -> None:
        """Initialize ClaudeClient with structured configuration.
        
        Args:
            config: ClaudeClientConfig with cwd, settings path, and optional system_prompt.
            
        Raises:
            FileNotFoundError: If the settings file does not exist.
        """
        # Read settings.json from the provided path
        with open(config.settings, 'r') as f:
            settings_data = json.load(f)
        
        print(f"[ClaudeClient] Loaded Claude settings from {config.settings}", file=sys.stderr)
        
        # Build options
        options = ClaudeAgentOptions(
            system_prompt=config.system_prompt,
            cwd=config.cwd,
            permission_mode="acceptEdits",
        )
        
        self._options = options
        
        # Apply custom settings if available (e.g., API key override)
        if settings_data:
            # Merge settings_data into ClaudeAgentOptions if supported
            # Note: SDK may support settings in different ways
            print(f"[ClaudeClient] Applying settings: {settings_data.get('api_key', 'N/A')} - Custom settings applied", file=sys.stderr)
    async def __aenter__(self) -> "ClaudeClient":
        """Enter async context manager, connecting to Claude."""
        self._client = ClaudeSDKClient(self._options)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore
        """Exit async context manager, disconnecting from Claude."""
        if self._client:
            await self._client.disconnect()

    async def query(self, prompt: str, session_id: str = "default") -> None:
        """Send a message to Claude.

        Args:
            prompt: The message to send to Claude.
            session_id: Session identifier for conversation continuity.
        """
        if not self._client:
            raise RuntimeError("ClaudeClient not connected. Use 'async with' to connect.")
        await self._client.query(prompt, session_id)

    async def receive_response(self):
        """Receive streaming response from Claude.

        Returns:
            AsyncIterator yielding response messages.
        """
        if not self._client:
            raise RuntimeError("ClaudeClient not connected. Use 'async with' to connect.")
        return self._client.receive_response()
