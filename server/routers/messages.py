"""Message API endpoints with AI integration."""

import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db_session
from services import MessageService
from claude_client import ClaudeClientConfig


router = APIRouter(prefix="/messages", tags=["messages"])


class MessageCreate(BaseModel):
    """Schema for creating a message."""
    message_unique_id: str
    session_unique_id: str
    data: dict


class MessageUpdate(BaseModel):
    """Schema for updating a message."""
    data: Optional[dict] = None


class MessageResponse(BaseModel):
    """Schema for message response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    message_unique_id: str
    session_unique_id: str
    time_created: int
    time_updated: int
    data: str


class AISendRequest(BaseModel):
    """Schema for AI send request."""
    prompt: str
    session_unique_id: str
    cwd: str
    settings: str
    system_prompt: str = "You are a helpful coding assistant"


class AISendResponse(BaseModel):
    """Schema for AI send response metadata."""
    session_unique_id: str
    status: str


@router.get("/", response_model=List[MessageResponse])
async def list_messages(
    session_unique_id: str,
    offset: int = 0,
    limit: int = 100,
    last_message_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db_session)
):
    """List messages for a session with pagination.
    
    Args:
        session_unique_id: The unique identifier of the session (required).
        offset: Offset for pagination (default: 0).
        limit: Maximum number of results (default: 100).
        last_message_id: If provided, only return messages with id > this value.
        
    Returns:
        List of messages belonging to the session.
    """
    service = MessageService(db)
    
    if last_message_id is not None:
        messages = await service.list_messages_after_id(
            session_unique_id=session_unique_id,
            last_message_id=last_message_id,
            limit=limit
        )
    else:
        messages = await service.list_messages(
            session_unique_id=session_unique_id,
            offset=offset,
            limit=limit
        )
    return messages


@router.get("/{message_unique_id}", response_model=MessageResponse)
async def get_message(
    message_unique_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Get a message by its unique identifier.
    
    Args:
        message_unique_id: The unique identifier of the message.
        
    Returns:
        The message if found.
        
    Raises:
        HTTPException: 404 if message not found.
    """
    service = MessageService(db)
    message = await service.get_message_by_unique_id(message_unique_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    return message


@router.post("/send")
async def send_ai_prompt(
    request: AISendRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """Send a prompt to AI and return streaming response.
    
    This endpoint receives a user prompt and sends it to the Claude AI,
    returning a streaming response using Server-Sent Events (SSE) format.
    
    Args:
        request: AI send request containing prompt, session info, and client config.
        
    Returns:
        StreamingResponse with AI response chunks in SSE format.
    """
    service = MessageService(db)
    
    client_config = ClaudeClientConfig(
        cwd=request.cwd,
        settings=request.settings,
        system_prompt=request.system_prompt
    )
    
    async def generate_stream():
        """Generate SSE stream from AI responses."""
        try:
            async for chunk in service.send_ai_prompt(
                prompt=request.prompt,
                session_unique_id=request.session_unique_id,
                client_config=client_config
            ):
                # Serialize chunk to JSON for SSE
                if hasattr(chunk, '__dict__'):
                    # Handle object with attributes
                    data = json.dumps({
                        "type": "chunk",
                        "content": str(chunk)
                    }, default=str)
                elif isinstance(chunk, (dict, list, str, int, float, bool)):
                    # Handle JSON-serializable types
                    data = json.dumps({
                        "type": "chunk",
                        "content": chunk
                    })
                else:
                    # Handle other types
                    data = json.dumps({
                        "type": "chunk",
                        "content": str(chunk)
                    })
                yield f"data: {data}\n\n"
            
            # Send completion event
            done_data = json.dumps({
                "type": "done",
                "session_unique_id": request.session_unique_id
            })
            yield f"data: {done_data}\n\n"
        except Exception as e:
            # Send error event
            error_data = json.dumps({
                "type": "error",
                "message": str(e)
            })
            yield f"data: {error_data}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )


@router.put("/{message_unique_id}", response_model=MessageResponse)
async def update_message(
    message_unique_id: str,
    message_data: MessageUpdate,
    db: AsyncSession = Depends(get_db_session)
):
    """Update a message's data.
    
    Args:
        message_unique_id: The unique identifier of the message to update.
        message_data: New message data.
        
    Returns:
        Updated message.
        
    Raises:
        HTTPException: 404 if message not found.
    """
    service = MessageService(db)
    
    update_kwargs = {}
    if message_data.data is not None:
        update_kwargs["data"] = message_data.data
    
    message = await service.update_message(
        message_unique_id=message_unique_id,
        **update_kwargs
    )
    
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    return message


@router.delete("/{message_unique_id}", status_code=204)
async def delete_message(
    message_unique_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Delete a message.
    
    Args:
        message_unique_id: The unique identifier of the message to delete.
        
    Returns:
        204 No Content on success.
        
    Raises:
        HTTPException: 404 if message not found.
    """
    service = MessageService(db)
    deleted = await service.delete_message(message_unique_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Message not found")
