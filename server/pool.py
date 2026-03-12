#!/usr/bin/env python3
"""Connection pool manager for ClaudeClient instances.

Provides session-level connection pooling with:
- Per-session client management (keyed by session_ulid)
- Concurrent access handling with asyncio.Lock per session
- Idle connection cleanup (configurable timeout)
"""

import asyncio
import time
from dataclasses import dataclass, field
from typing import Dict, Optional

from claude_client import ClaudeClient, ClaudeClientConfig


@dataclass
class PoolEntry:
    """Entry in the connection pool tracking a ClaudeClient instance.
    
    Attributes:
        client: The ClaudeClient instance for this session.
        last_used: Unix timestamp of last access.
        in_use: Whether the client is currently being used.
    """
    client: ClaudeClient
    last_used: float = field(default_factory=time.time)
    in_use: bool = False


class ClaudeClientPool:
    """Manages ClaudeClient instances per session with connection pooling.
    
    Provides:
    - Per-session client management (keyed by session_ulid)
    - Concurrent access handling with asyncio.Lock per session
    - Idle connection cleanup (configurable timeout, default 5 minutes)
    
    Example:
        async with ClaudeClientPool() as pool:
            config = ClaudeClientConfig(cwd="/path", settings="/path/settings.json")
            client = await pool.get_client("session_ulid_123", config)
            # Use client...
            await pool.release_client("session_ulid_123")
    """
    
    def __init__(self, idle_timeout_seconds: int = 300) -> None:
        """Initialize the connection pool.
        
        Args:
            idle_timeout_seconds: Seconds before idle clients are cleaned up.
                                  Default is 300 (5 minutes).
        """
        self.idle_timeout_seconds = idle_timeout_seconds
        self._pool: Dict[str, PoolEntry] = {}
        self._locks: Dict[str, asyncio.Lock] = {}
        self._pool_lock = asyncio.Lock()
    
    async def __aenter__(self) -> "ClaudeClientPool":
        """Enter async context manager."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore
        """Exit async context manager, cleaning up all clients."""
        await self._cleanup_all()
    
    def _get_or_create_lock(self, session_ulid: str) -> asyncio.Lock:
        """Get or create a lock for a specific session.
        
        Args:
            session_ulid: Session identifier.
            
        Returns:
            asyncio.Lock for this session.
        """
        if session_ulid not in self._locks:
            self._locks[session_ulid] = asyncio.Lock()
        return self._locks[session_ulid]
    
    async def get_client(
        self, 
        session_ulid: str, 
        config: ClaudeClientConfig
    ) -> ClaudeClient:
        """Get or create a ClaudeClient for the given session.
        
        If a client already exists for this session, reuses it.
        Otherwise, creates a new client and connects it.
        
        Args:
            session_ulid: Unique session identifier (ULID format).
            config: Configuration for creating new client if needed.
            
        Returns:
            ClaudeClient instance ready for use.
        """
        lock = self._get_or_create_lock(session_ulid)
        
        async with lock:
            if session_ulid in self._pool:
                # Reuse existing client
                entry = self._pool[session_ulid]
                entry.last_used = time.time()
                entry.in_use = True
                return entry.client
            
            # Create new client
            client = ClaudeClient(config)
            await client.__aenter__()
            
            self._pool[session_ulid] = PoolEntry(
                client=client,
                last_used=time.time(),
                in_use=True
            )
            
            return client
    
    async def release_client(
        self, 
        session_ulid: str, 
        disconnect: bool = False
    ) -> None:
        """Release a client back to the pool.
        
        Marks the client as not in use and updates the last_used timestamp.
        Optionally disconnects and removes the client from the pool.
        
        Args:
            session_ulid: Session identifier to release.
            disconnect: If True, disconnects and removes the client from pool.
        """
        if session_ulid not in self._pool:
            return
        
        lock = self._get_or_create_lock(session_ulid)
        
        async with lock:
            if session_ulid not in self._pool:
                return
            
            if disconnect:
                entry = self._pool.pop(session_ulid)
                try:
                    await entry.client.__aexit__(None, None, None)
                except Exception:
                    pass  # Ignore disconnect errors
            else:
                entry = self._pool[session_ulid]
                entry.last_used = time.time()
                entry.in_use = False
    
    async def cleanup_idle(self) -> int:
        """Remove clients that have been idle beyond the timeout.
        
        Scans the pool for clients that:
        - Are not currently in use (in_use=False)
        - Have been idle longer than idle_timeout_seconds
        
        Returns:
            Number of clients removed.
        """
        now = time.time()
        to_remove = []
        
        async with self._pool_lock:
            for session_ulid, entry in list(self._pool.items()):
                if entry.in_use:
                    continue
                
                idle_time = now - entry.last_used
                if idle_time > self.idle_timeout_seconds:
                    to_remove.append(session_ulid)
            
            for session_ulid in to_remove:
                entry = self._pool.pop(session_ulid, None)
                if entry:
                    try:
                        await entry.client.__aexit__(None, None, None)
                    except Exception:
                        pass  # Ignore disconnect errors
        
        return len(to_remove)
    
    async def _cleanup_all(self) -> None:
        """Disconnect and remove all clients from the pool."""
        async with self._pool_lock:
            session_ulids = list(self._pool.keys())
            
            for session_ulid in session_ulids:
                entry = self._pool.pop(session_ulid, None)
                if entry:
                    try:
                        await entry.client.__aexit__(None, None, None)
                    except Exception:
                        pass  # Ignore disconnect errors
    
    def pool_size(self) -> int:
        """Get total number of clients in the pool.
        
        Returns:
            Total count of clients (both in-use and idle).
        """
        return len(self._pool)
    
    def active_count(self) -> int:
        """Get number of clients currently in use.
        
        Returns:
            Count of clients with in_use=True.
        """
        return sum(1 for entry in self._pool.values() if entry.in_use)
