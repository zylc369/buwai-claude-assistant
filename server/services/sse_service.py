"""Server-Sent Events (SSE) service for real-time streaming.

Provides SSE-formatted streaming output wrapping ClaudeClient responses.
Supports session-level streaming for real-time AI response delivery.
"""

import asyncio
import json
from collections import defaultdict
from enum import Enum
from typing import Any, AsyncGenerator, AsyncIterator, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from repositories.conversation_session_repository import ConversationSessionRepository
from claude_client import ClaudeClient, ClaudeClientConfig
from pool import ClaudeClientPool
from logger import get_logger

logger = get_logger(__name__)


class SSEEventType(str, Enum):
    """SSE event types for AI streaming."""

    MESSAGE = "message"
    ERROR = "error"
    DONE = "done"
    TOOL_USE = "tool_use"
    THINKING = "thinking"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    HEARTBEAT = "heartbeat"


class SSEService:
    def __init__(self, db: Optional[AsyncSession] = None):
        logger.debug(f"SSEService.__init__ called with db={db is not None}")
        self.db = db
        self._session_repository = ConversationSessionRepository(db) if db else None
        self._active_streams: dict[str, asyncio.Queue] = defaultdict(asyncio.Queue)
        logger.debug(f"SSEService.__init__ completed")
    
    async def get_session_stream(
        self,
        session_unique_id: str
    ) -> AsyncGenerator[str, None]:
        logger.debug(f"get_session_stream called with session_unique_id={session_unique_id}")
        if self._session_repository is not None:
            session = await self._session_repository.get_by_unique_id(session_unique_id)
            if not session:
                logger.error(f"get_session_stream failed: Session '{session_unique_id}' not found")
                yield self._format_event("error", {"message": f"Session '{session_unique_id}' not found"})
                return

        logger.info(f"Business decision: creating SSE stream for session {session_unique_id}")
        queue = self._active_streams[session_unique_id]

        try:
            # Send initial connected event
            logger.info(f"Business decision: sending connected event for session {session_unique_id}")
            yield self._format_event("connected", {
                "session_id": session_unique_id,
                "message": "SSE stream connected"
            })

            while True:
                try:
                    # Wait for events with timeout for heartbeat
                    event = await asyncio.wait_for(
                        queue.get(),
                        timeout=30.0
                    )
                    yield event
                except asyncio.TimeoutError:
                    # Send heartbeat to keep connection alive
                    logger.debug(f"get_session_stream sending heartbeat for session {session_unique_id}")
                    yield self._format_event("heartbeat", {
                        "message": "Connection alive"
                    })
        except asyncio.CancelledError:
            # Client disconnected
            logger.info(f"get_session_stream cancelled, client disconnected from session {session_unique_id}")
            yield self._format_event("disconnected", {
                "message": "Stream closed"
            })
        finally:
            # Cleanup if this was the last stream for this session
            if queue.empty():
                if session_unique_id in self._active_streams:
                    del self._active_streams[session_unique_id]
                    logger.debug(f"get_session_stream cleaned up stream for session {session_unique_id}")
    
    async def push_event(
        self,
        session_unique_id: str,
        event_type: str,
        data: dict
    ) -> bool:
        """Push an event to a session's SSE stream.

        Args:
            session_unique_id: The unique identifier of the session.
            event_type: The type of event (e.g., 'message', 'ai_response').
            data: The event data payload.

        Returns:
            True if event was pushed successfully, False if no active stream.
        """
        logger.debug(f"push_event called with session_unique_id={session_unique_id}, event_type={event_type}")
        if session_unique_id not in self._active_streams:
            logger.debug(f"push_event completed, no active stream for session {session_unique_id}")
            return False

        logger.info(f"Business decision: pushing {event_type} event to session {session_unique_id}")
        queue = self._active_streams[session_unique_id]
        event = self._format_event(event_type, data)
        await queue.put(event)
        logger.debug(f"push_event completed")
        return True
    
    def _format_event(self, event_type: str, data: dict) -> str:
        event_line = f"event: {event_type}\n"
        data_line = f"data: {json.dumps(data, ensure_ascii=False)}\n"
        return f"{event_line}{data_line}\n"
    
    def send_event(
        self,
        event_type: str,
        data: Any,
        event_id: Optional[str] = None,
        retry: Optional[int] = None
    ) -> str:
        lines = []
        
        if event_id is not None:
            lines.append(f"id: {event_id}")
        
        if retry is not None:
            lines.append(f"retry: {retry}")
        
        lines.append(f"event: {event_type}")
        
        if isinstance(data, str):
            for line in data.split("\n"):
                lines.append(f"data: {line}")
        else:
            lines.append(f"data: {json.dumps(data, ensure_ascii=False)}")
        
        return "\n".join(lines) + "\n\n"
    
    def complete_stream(self) -> str:
        return self.send_event(
            event_type=SSEEventType.DONE.value,
            data={"status": "complete"}
        )
    
    def _response_to_sse(self, response: Any) -> str:
        if hasattr(response, "type"):
            response_type = response.type
            
            if response_type == "text":
                text = getattr(response, "text", str(response))
                return self.send_event(
                    event_type=SSEEventType.MESSAGE.value,
                    data={"text": text}
                )
            elif response_type == "tool_use":
                tool_name = getattr(response, "name", "unknown")
                tool_input = getattr(response, "input", {})
                return self.send_event(
                    event_type=SSEEventType.TOOL_USE.value,
                    data={"name": tool_name, "input": tool_input}
                )
            elif response_type == "thinking":
                thinking_text = getattr(response, "thinking", str(response))
                return self.send_event(
                    event_type=SSEEventType.THINKING.value,
                    data={"thinking": thinking_text}
                )
        
        return self.send_event(
            event_type=SSEEventType.MESSAGE.value,
            data={"text": str(response)}
        )
    
    def _error_to_sse(self, error_message: str) -> str:
        return self.send_event(
            event_type=SSEEventType.ERROR.value,
            data={"error": error_message}
        )
    
    async def create_stream(
        self,
        prompt: str,
        session_unique_id: str,
        client_config: ClaudeClientConfig,
        pool: Optional[ClaudeClientPool] = None
    ) -> AsyncGenerator[str, None]:
        logger.debug(f"create_stream called with session_unique_id={session_unique_id}")
        logger.info(f"AI operation: creating SSE stream for prompt of length {len(prompt)} characters")
        try:
            if pool is not None:
                client = await pool.get_client(session_unique_id, client_config)
                try:
                    logger.info(f"AI operation: querying AI client with pool for session {session_unique_id}")
                    await client.query(prompt, session_unique_id)
                    async for response in await client.receive_response():
                        yield self._response_to_sse(response)
                    yield self.complete_stream()
                finally:
                    await pool.release_client(session_unique_id)
            else:
                async with ClaudeClient(client_config) as client:
                    logger.info(f"AI operation: querying AI client without pool for session {session_unique_id}")
                    await client.query(prompt, session_unique_id)
                    async for response in await client.receive_response():
                        yield self._response_to_sse(response)
                    yield self.complete_stream()
            logger.debug(f"create_stream completed successfully")
        except Exception as e:
            logger.error(f"create_stream failed: {str(e)}")
            yield self._error_to_sse(str(e))
    
    async def wrap_ai_response(
        self,
        response_iterator: AsyncIterator[Any]
    ) -> AsyncGenerator[str, None]:
        logger.debug(f"wrap_ai_response called")
        logger.info(f"AI operation: wrapping AI response iterator")
        try:
            async for response in response_iterator:
                yield self._response_to_sse(response)
            yield self.complete_stream()
            logger.debug(f"wrap_ai_response completed successfully")
        except Exception as e:
            logger.error(f"wrap_ai_response failed: {str(e)}")
            yield self._error_to_sse(str(e))
