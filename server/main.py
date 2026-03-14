#!/usr/bin/env python3
"""Main entry point for Claude SDK example."""

import argparse
import asyncio
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Union, List, Optional

from logger import get_logger, setup_logging, shutdown_logging

try:
    from claude_client import ClaudeClient
except ImportError:
    ClaudeClient = None  # type: ignore

try:
    from claude_agent_sdk import (
        TextBlock, ToolUseBlock, ThinkingBlock,
        AssistantMessage, ResultMessage
    )
except ImportError:
    # For testing without SDK installed
    TextBlock = None  # type: ignore
    ToolUseBlock = None  # type: ignore
    ThinkingBlock = None  # type: ignore
    AssistantMessage = None  # type: ignore
    ResultMessage = None  # type: ignore

logger = get_logger(__name__)


@dataclass
class LoggingConfig:
    enabled: bool = True
    level: str = "INFO"
    dir: str = "logs"
    format: str = "[时间：%(asctime)s][进程ID:%(process)d][线程ID:%(thread)d][%(class_name)s][%(funcName)s][%(request_id)s] - %(message)s"
    date_format: str = "%Y-%m-%d %H-%M-%S"


def process_message(
    message_block: Union["TextBlock", "ToolUseBlock", "AssistantMessage", "ResultMessage", object],
    stream: bool = True,
    verbose: bool = True
) -> str:
    """
    Process and format message blocks for output.

    Args:
        message_block: Message block to process (TextBlock, ToolUseBlock, AssistantMessage, etc.)
        stream: If True, print immediately. If False, return formatted string.
        verbose: If True, show tool use details. If False, hide them.

    Returns:
        Formatted string (empty string in stream mode)
    """
    msg_type = type(message_block).__name__
    logger.debug(f"Processing message of type: {msg_type}")

    result = ""

    # Handle AssistantMessage - extract content blocks (only in streaming mode)
    if AssistantMessage and isinstance(message_block, AssistantMessage):
        # In streaming mode, show content as it arrives
        if stream and hasattr(message_block, 'content') and message_block.content:
            for block in message_block.content:
                block_result = process_message(block, stream=stream, verbose=verbose)
                if block_result:
                    result += block_result
    
    # Handle ResultMessage - show final result (only in non-streaming mode)
    elif ResultMessage and isinstance(message_block, ResultMessage):
        # In streaming mode, content was already displayed via AssistantMessage
        # Only show ResultMessage in non-streaming mode
        if not stream and hasattr(message_block, 'result') and message_block.result:
            result = message_block.result
    
    # Handle TextBlock
    elif TextBlock and isinstance(message_block, TextBlock):
        if stream:
            print(message_block.text, end="", flush=True)
        else:
            result = message_block.text
    
    # Handle ThinkingBlock (show in verbose mode)
    elif ThinkingBlock and isinstance(message_block, ThinkingBlock):
        if verbose:
            if stream:
                print(f"[Thinking: {message_block.thinking[:100]}...]", file=sys.stderr)
            else:
                result = f"[Thinking: {message_block.thinking[:100]}...]"
    
    # Handle ToolUseBlock
    elif ToolUseBlock and isinstance(message_block, ToolUseBlock):
        if verbose:
            tool_info = f"\n[Tool: {message_block.name}]\nInput: {message_block.input}\n"
            if stream:
                print(tool_info)
            else:
                result = tool_info
    
    # Unknown message type - log and skip
    else:
        if verbose:
            msg_type = type(message_block).__name__
            if msg_type not in ('SystemMessage', 'UserMessage'):
                print(f"[Unknown message type: {msg_type}]", file=sys.stderr)
    
    return result


def process_messages(
    messages: List[Union["TextBlock", "ToolUseBlock", object]],
    verbose: bool = True
) -> str:
    """
    Process multiple messages in non-streaming mode.
    
    Args:
        messages: List of message blocks
        verbose: If True, show tool use details
    
    Returns:
        Formatted string of all messages
    """
    results: List[str] = []
    for message in messages:
        result = process_message(message, stream=False, verbose=verbose)
        if result:
            results.append(result)
    return "".join(results)


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments for the Claude SDK example.

    Returns:
        argparse.Namespace: Parsed arguments with stream and verbose settings.

    Supported arguments:
        --stream, --no-stream: Enable or disable streaming output (default: stream=True)
        --verbose, --quiet: Enable or disable verbose mode (default: verbose=True)
    """
    parser = argparse.ArgumentParser(
        description="Claude SDK example - Demonstrates parameter parsing with stream and verbose modes."
    )

    # Create mutually exclusive group for stream argument
    stream_group = parser.add_mutually_exclusive_group()
    stream_group.add_argument(
        "--stream",
        action="store_true",
        default=True,
        help="Enable streaming output (default)"
    )
    stream_group.add_argument(
        "--no-stream",
        action="store_false",
        dest="stream",
        help="Disable streaming output"
    )

    # Create mutually exclusive group for verbose argument
    verbose_group = parser.add_mutually_exclusive_group()
    verbose_group.add_argument(
        "--verbose",
        action="store_true",
        default=True,
        help="Show verbose output (default)"
    )
    verbose_group.add_argument(
        "--quiet",
        action="store_false",
        dest="verbose",
        help="Hide verbose output"
    )

    # Additional required/optional CLI arguments
    parser.add_argument(
        "--cwd",
        required=True,
        help="Working directory (required)"
    )
    parser.add_argument(
        "--settings",
        default="~/.claude/settings.json",
        help="Path to Claude settings.json file (default: ~/.claude/settings.json)"
    )

    args = parser.parse_args()
    # Expand the settings path (e.g., ~) to an absolute path string
    args.settings = str(Path(args.settings).expanduser())
    return args


async def repl_loop(cwd: str, settings: str, stream: bool = True, verbose: bool = True) -> None:
    """
    REPL (Read-Eval-Print Loop) for interactive Claude chat.

    Args:
        cwd: Working directory to pass to ClaudeClientConfig
        settings: Path to Claude settings.json to pass to ClaudeClientConfig
        stream: Enable streaming output (default: True)
        verbose: Show verbose output including tool calls (default: True)
    """
    print("Claude SDK REPL - Type 'exit' or 'quit' to exit, Ctrl+D to exit", file=sys.stderr)
    print("Press Ctrl+C to interrupt current operation", file=sys.stderr)
    print(file=sys.stderr)

    if ClaudeClient is None:
        print("Error: ClaudeClient not available. Make sure claude_client.py exists.", file=sys.stderr)
        print("Falling back to demo mode (no API calls).", file=sys.stderr)
        print(file=sys.stderr)
        while True:
            try:
                user_input = input("> ")
            except EOFError:
                print("\nGoodbye!", file=sys.stderr)
                logger.info("Exiting due to EOF (Ctrl+D)")
                break
            except KeyboardInterrupt:
                print("\nGoodbye!", file=sys.stderr)
                logger.info("Exiting due to KeyboardInterrupt (Ctrl+C)")
                break
            # Handle exit commands
            if user_input.strip().lower() in ("exit", "quit"):
                print("Goodbye!", file=sys.stderr)
                logger.info("Exiting via exit command")
                break
            # Skip empty input
            if not user_input.strip():
                continue
            # Demo mode - just echo back
            truncated_input = user_input[:50] + "..." if len(user_input) > 50 else user_input
            logger.debug(f"Demo mode input: {truncated_input}")
            print(f"[Demo mode] You said: {user_input}")
        return

    # Normal mode with ClaudeClient
    try:
        # Example: Use ClaudeClient with structured configuration
        from claude_client import ClaudeClientConfig
        config = ClaudeClientConfig(
            system_prompt="You are a helpful coding assistant",
            cwd=cwd,
            settings=settings
        )
        async with ClaudeClient(config) as client:
            while True:
                logger.debug("REPL loop iteration")
                try:
                    user_input = input("> ")
                except EOFError:
                    print("\nGoodbye!", file=sys.stderr)
                    logger.info("Exiting due to EOF (Ctrl+D)")
                    break
                except KeyboardInterrupt:
                    print("\nGoodbye!", file=sys.stderr)
                    logger.info("Exiting due to KeyboardInterrupt (Ctrl+C)")
                    break
                # Handle exit commands
                if user_input.strip().lower() in ("exit", "quit"):
                    print("Goodbye!", file=sys.stderr)
                    logger.info("Exiting via exit command")
                    break
                # Skip empty input
                if not user_input.strip():
                    continue
                truncated_input = user_input[:50] + "..." if len(user_input) > 50 else user_input
                logger.debug(f"User input: {truncated_input}")
                try:
                    # Send message to Claude
                    await client.query(user_input)
                    if stream:
                        async for chunk in await client.receive_response():
                            process_message(chunk, stream=True, verbose=verbose)
                        print()  # New line after streaming output
                    else:
                        chunks = []
                        async for chunk in await client.receive_response():
                            chunks.append(chunk)
                        result = process_messages(chunks, verbose=verbose)
                        print(result)
                except Exception as e:
                    logger.error(f"Error processing message: {e}", exc_info=True)
                    print(f"\nError: {e}", file=sys.stderr)
                    print("Please try again or type 'exit' to quit.", file=sys.stderr)
                    continue
    except KeyboardInterrupt:
        print("\nGoodbye!", file=sys.stderr)
        logger.info("REPL interrupted by KeyboardInterrupt (Ctrl+C)")
    except Exception as e:
        logger.error(f"Fatal error in REPL: {e}", exc_info=True)
        print(f"Fatal error: {e}", file=sys.stderr)


def main() -> None:
    """Main function to run the Claude SDK REPL."""
    args = parse_args()

    config = LoggingConfig()
    setup_logging(config)

    try:
        logger.info(f"Application started with args: cwd={args.cwd}, settings={args.settings}, stream={args.stream}, verbose={args.verbose}")
        asyncio.run(
            repl_loop(
                cwd=args.cwd,
                settings=args.settings,
                stream=args.stream,
                verbose=args.verbose,
            )
        )
    finally:
        logger.info("Application shutting down")
        shutdown_logging()


if __name__ == "__main__":
    main()
