"""Server-Sent Events (SSE) endpoint for real-time updates."""

import asyncio
import json
from typing import AsyncGenerator
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from logger import get_logger


router = APIRouter(prefix="/events", tags=["events"])
logger = get_logger(__name__)


async def event_stream() -> AsyncGenerator[str, None]:
    """Generate SSE event stream.
    
    This is a basic implementation. In production, you would:
    - Connect to a message broker (Redis, RabbitMQ)
    - Subscribe to specific channels (user updates, task updates, etc.)
    - Send events based on actual data changes
    """
    while True:
        # Send a heartbeat every 30 seconds
        data = json.dumps({"type": "heartbeat", "message": "Connection alive"})
        yield f"data: {data}\n\n"
        
        await asyncio.sleep(30)


@router.get("/stream")
async def stream_events(request: Request):
    """SSE endpoint for real-time updates.

    Returns:
        StreamingResponse with SSE formatted events.

    Example event format:
        data: {"type": "task_update", "task_id": 123, "status": "completed"}
    """
    logger.info(f"stream_events called: {request.method} {request.url.path}")

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
