#!/usr/bin/env python3
"""Claude SDK client wrapper with async context manager support."""

import sys
import json

from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
from dataclasses import dataclass
from logger import get_logger

logger = get_logger(__name__)



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
    system_prompt: str = "You are a helpful coding assistant"
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
        try:
            logger.info(f"Initializing ClaudeClient with settings from {config.settings}")
            logger.debug(f"Configuration: cwd={config.cwd}, system_prompt_length={len(config.system_prompt)}")

            # Build options
            options = ClaudeAgentOptions(
                system_prompt=config.system_prompt,
                cwd=config.cwd,
                permission_mode="acceptEdits",
                settings=config.settings
            )

            self._options = options
            logger.info("ClaudeClient initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ClaudeClient: {e}", exc_info=True)
            raise
    async def __aenter__(self) -> "ClaudeClient":
        """Enter async context manager, connecting to Claude."""
        try:
            logger.info("Connecting to Claude SDK")
            self._client = ClaudeSDKClient(self._options)
            await self._client.connect()
            logger.info("Successfully connected to Claude SDK")
            return self
        except Exception as e:
            logger.error(f"Failed to connect to Claude SDK: {e}", exc_info=True)
            raise

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore
        """Exit async context manager, disconnecting from Claude."""
        try:
            logger.info("Disconnecting from Claude SDK")
            if self._client:
                await self._client.disconnect()
                logger.info("Successfully disconnected from Claude SDK")
            if exc_type:
                logger.error(f"Exiting context with exception: {exc_type.__name__}: {exc_val}")
        except Exception as e:
            logger.error(f"Error during disconnect: {e}", exc_info=True)

    async def query(self, prompt: str, session_id: str = "default") -> None:
        """Send a message to Claude.

        Args:
            prompt: The message to send to Claude.
            session_id: Session identifier for conversation continuity.
        """
        try:
            truncated_prompt = prompt[:100] + "..." if len(prompt) > 100 else prompt
            logger.info(f"Sending query (session_id={session_id}): {truncated_prompt}")
            logger.debug(f"Full query: {prompt}")

            if not self._client:
                raise RuntimeError("ClaudeClient not connected. Use 'async with' to connect.")
            await self._client.query(prompt, session_id)
        except Exception as e:
            logger.error(f"Failed to send query: {e}", exc_info=True)
            raise

    async def receive_response(self):
        """Receive streaming response from Claude.

        Returns:
            AsyncIterator yielding response messages.
        """
        try:
            logger.info("Receiving response from Claude SDK")
            if not self._client:
                raise RuntimeError("ClaudeClient not connected. Use 'async with' to connect.")
            return self._client.receive_response()
        except Exception as e:
            logger.error(f"Failed to receive response: {e}", exc_info=True)
            raise
