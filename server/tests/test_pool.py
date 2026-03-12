#!/usr/bin/env python3
"""Unit tests for pool.py ClaudeClientPool."""

import asyncio
import json
import pytest
import tempfile
import time
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

from claude_client import ClaudeClientConfig, ClaudeClient
from pool import ClaudeClientPool, PoolEntry


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def temp_settings():
    """Create a temporary settings file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({"api_key": "test-key"}, f)
        yield f.name
    Path(f.name).unlink()


@pytest.fixture
def client_config(temp_settings):
    """Create a ClaudeClientConfig for testing."""
    return ClaudeClientConfig(
        cwd="/tmp/test",
        settings=temp_settings,
        system_prompt="Test prompt"
    )


@pytest.fixture
def pool():
    """Create a ClaudeClientPool for testing."""
    return ClaudeClientPool(idle_timeout_seconds=300)


# =============================================================================
# PoolEntry Tests
# =============================================================================

class TestPoolEntry:
    """Tests for PoolEntry dataclass."""

    def test_pool_entry_creation(self):
        """Test PoolEntry stores client and metadata."""
        mock_client = MagicMock()
        entry = PoolEntry(
            client=mock_client,
            last_used=time.time(),
            in_use=True
        )
        assert entry.client == mock_client
        assert entry.last_used > 0
        assert entry.in_use is True

    def test_pool_entry_default_in_use(self):
        """Test PoolEntry default in_use is False."""
        mock_client = MagicMock()
        entry = PoolEntry(
            client=mock_client,
            last_used=time.time()
        )
        assert entry.in_use is False


# =============================================================================
# ClaudeClientPool Initialization Tests
# =============================================================================

class TestClaudeClientPoolInit:
    """Tests for ClaudeClientPool initialization."""

    def test_default_initialization(self):
        """Test pool initializes with default idle timeout."""
        pool = ClaudeClientPool()
        assert pool.idle_timeout_seconds == 300  # 5 minutes

    def test_custom_idle_timeout(self):
        """Test pool initializes with custom idle timeout."""
        pool = ClaudeClientPool(idle_timeout_seconds=60)
        assert pool.idle_timeout_seconds == 60

    def test_empty_pool_on_init(self):
        """Test pool is empty after initialization."""
        pool = ClaudeClientPool()
        assert len(pool._pool) == 0
        assert len(pool._locks) == 0


# =============================================================================
# get_client Tests
# =============================================================================

class TestGetClient:
    """Tests for ClaudeClientPool.get_client method."""

    @pytest.mark.asyncio
    async def test_get_client_creates_new_client(self, pool, client_config):
        """Test get_client creates new client for new session_ulid."""
        session_ulid = "01ARZ3NDEKTSV4RRFFQ69G5FAV"
        
        with patch('pool.ClaudeClient') as MockClient:
            mock_instance = AsyncMock()
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_instance
            
            client = await pool.get_client(session_ulid, client_config)
            
            assert client is not None
            assert session_ulid in pool._pool
            MockClient.assert_called_once_with(client_config)

    @pytest.mark.asyncio
    async def test_get_client_reuses_existing_client(self, pool, client_config):
        """Test get_client reuses existing client for same session_ulid."""
        session_ulid = "01ARZ3NDEKTSV4RRFFQ69G5FAV"
        
        with patch('pool.ClaudeClient') as MockClient:
            mock_instance = AsyncMock()
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_instance
            
            client1 = await pool.get_client(session_ulid, client_config)
            client2 = await pool.get_client(session_ulid, client_config)
            
            # Should reuse same client, only create once
            MockClient.assert_called_once_with(client_config)
            assert client1 is client2

    @pytest.mark.asyncio
    async def test_get_client_different_sessions(self, pool, client_config):
        """Test get_client creates different clients for different session_ulids."""
        session_ulid_1 = "01ARZ3NDEKTSV4RRFFQ69G5FAV"
        session_ulid_2 = "01ARZ3NDEKTSV4RRFFQ69G5FAW"
        
        with patch('pool.ClaudeClient') as MockClient:
            mock_instance_1 = AsyncMock()
            mock_instance_1.__aenter__ = AsyncMock(return_value=mock_instance_1)
            mock_instance_1.__aexit__ = AsyncMock(return_value=None)
            
            mock_instance_2 = AsyncMock()
            mock_instance_2.__aenter__ = AsyncMock(return_value=mock_instance_2)
            mock_instance_2.__aexit__ = AsyncMock(return_value=None)
            
            MockClient.side_effect = [mock_instance_1, mock_instance_2]
            
            client1 = await pool.get_client(session_ulid_1, client_config)
            client2 = await pool.get_client(session_ulid_2, client_config)
            
            # Should create different clients
            assert MockClient.call_count == 2
            assert len(pool._pool) == 2

    @pytest.mark.asyncio
    async def test_get_client_marks_in_use(self, pool, client_config):
        """Test get_client marks entry as in_use."""
        session_ulid = "01ARZ3NDEKTSV4RRFFQ69G5FAV"
        
        with patch('pool.ClaudeClient') as MockClient:
            mock_instance = AsyncMock()
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_instance
            
            await pool.get_client(session_ulid, client_config)
            
            entry = pool._pool[session_ulid]
            assert entry.in_use is True

    @pytest.mark.asyncio
    async def test_get_client_updates_last_used(self, pool, client_config):
        """Test get_client updates last_used timestamp."""
        session_ulid = "01ARZ3NDEKTSV4RRFFQ69G5FAV"
        
        with patch('pool.ClaudeClient') as MockClient:
            mock_instance = AsyncMock()
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_instance
            
            before = time.time()
            await pool.get_client(session_ulid, client_config)
            after = time.time()
            
            entry = pool._pool[session_ulid]
            assert before <= entry.last_used <= after


# =============================================================================
# release_client Tests
# =============================================================================

class TestReleaseClient:
    """Tests for ClaudeClientPool.release_client method."""

    @pytest.mark.asyncio
    async def test_release_client_marks_not_in_use(self, pool, client_config):
        """Test release_client marks entry as not in_use."""
        session_ulid = "01ARZ3NDEKTSV4RRFFQ69G5FAV"
        
        with patch('pool.ClaudeClient') as MockClient:
            mock_instance = AsyncMock()
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_instance
            
            await pool.get_client(session_ulid, client_config)
            assert pool._pool[session_ulid].in_use is True
            
            await pool.release_client(session_ulid)
            assert pool._pool[session_ulid].in_use is False

    @pytest.mark.asyncio
    async def test_release_client_updates_last_used(self, pool, client_config):
        """Test release_client updates last_used timestamp."""
        session_ulid = "01ARZ3NDEKTSV4RRFFQ69G5FAV"
        
        with patch('pool.ClaudeClient') as MockClient:
            mock_instance = AsyncMock()
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_instance
            
            await pool.get_client(session_ulid, client_config)
            original_time = pool._pool[session_ulid].last_used
            
            # Small delay to ensure time difference
            await asyncio.sleep(0.01)
            
            await pool.release_client(session_ulid)
            assert pool._pool[session_ulid].last_used > original_time

    @pytest.mark.asyncio
    async def test_release_client_nonexistent_session(self, pool):
        """Test release_client handles nonexistent session gracefully."""
        session_ulid = "01ARZ3NDEKTSV4RRFFQ69G5FAV"
        
        # Should not raise error
        await pool.release_client(session_ulid)
        assert session_ulid not in pool._pool

    @pytest.mark.asyncio
    async def test_release_client_disconnects_on_request(self, pool, client_config):
        """Test release_client can disconnect client when requested."""
        session_ulid = "01ARZ3NDEKTSV4RRFFQ69G5FAV"
        
        with patch('pool.ClaudeClient') as MockClient:
            mock_instance = AsyncMock()
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_instance.disconnect = AsyncMock()
            MockClient.return_value = mock_instance
            
            await pool.get_client(session_ulid, client_config)
            await pool.release_client(session_ulid, disconnect=True)
            
            # Entry should be removed after disconnect
            assert session_ulid not in pool._pool


# =============================================================================
# cleanup_idle Tests
# =============================================================================

class TestCleanupIdle:
    """Tests for ClaudeClientPool.cleanup_idle method."""

    @pytest.mark.asyncio
    async def test_cleanup_removes_idle_clients(self, pool, client_config):
        """Test cleanup_idle removes clients idle beyond timeout."""
        session_ulid = "01ARZ3NDEKTSV4RRFFQ69G5FAV"
        pool.idle_timeout_seconds = 0.1  # 100ms for testing
        
        with patch('pool.ClaudeClient') as MockClient:
            mock_instance = AsyncMock()
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_instance.disconnect = AsyncMock()
            MockClient.return_value = mock_instance
            
            await pool.get_client(session_ulid, client_config)
            await pool.release_client(session_ulid)
            
            # Wait for timeout
            await asyncio.sleep(0.15)
            
            removed_count = await pool.cleanup_idle()
            
            assert removed_count == 1
            assert session_ulid not in pool._pool

    @pytest.mark.asyncio
    async def test_cleanup_keeps_in_use_clients(self, pool, client_config):
        """Test cleanup_idle does not remove clients currently in use."""
        session_ulid = "01ARZ3NDEKTSV4RRFFQ69G5FAV"
        pool.idle_timeout_seconds = 0.1  # 100ms for testing
        
        with patch('pool.ClaudeClient') as MockClient:
            mock_instance = AsyncMock()
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_instance
            
            await pool.get_client(session_ulid, client_config)
            # Client is in_use=True (not released)
            
            # Wait for timeout
            await asyncio.sleep(0.15)
            
            removed_count = await pool.cleanup_idle()
            
            assert removed_count == 0
            assert session_ulid in pool._pool

    @pytest.mark.asyncio
    async def test_cleanup_keeps_recent_clients(self, pool, client_config):
        """Test cleanup_idle does not remove recently used clients."""
        session_ulid = "01ARZ3NDEKTSV4RRFFQ69G5FAV"
        pool.idle_timeout_seconds = 10  # 10 seconds
        
        with patch('pool.ClaudeClient') as MockClient:
            mock_instance = AsyncMock()
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_instance
            
            await pool.get_client(session_ulid, client_config)
            await pool.release_client(session_ulid)
            
            # Immediate cleanup should not remove
            removed_count = await pool.cleanup_idle()
            
            assert removed_count == 0
            assert session_ulid in pool._pool

    @pytest.mark.asyncio
    async def test_cleanup_empty_pool(self, pool):
        """Test cleanup_idle handles empty pool gracefully."""
        removed_count = await pool.cleanup_idle()
        assert removed_count == 0


# =============================================================================
# Concurrent Access Tests
# =============================================================================

class TestConcurrentAccess:
    """Tests for concurrent access handling."""

    @pytest.mark.asyncio
    async def test_concurrent_get_same_session(self, pool, client_config):
        """Test concurrent get_client calls for same session are serialized."""
        session_ulid = "01ARZ3NDEKTSV4RRFFQ69G5FAV"
        
        with patch('pool.ClaudeClient') as MockClient:
            mock_instance = AsyncMock()
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_instance
            
            # Simulate concurrent access
            results = await asyncio.gather(
                pool.get_client(session_ulid, client_config),
                pool.get_client(session_ulid, client_config),
                pool.get_client(session_ulid, client_config)
            )
            
            # Should only create one client
            MockClient.assert_called_once_with(client_config)
            assert all(r is results[0] for r in results)

    @pytest.mark.asyncio
    async def test_concurrent_get_different_sessions(self, pool, client_config):
        """Test concurrent get_client calls for different sessions work in parallel."""
        session_ulids = [
            "01ARZ3NDEKTSV4RRFFQ69G5FAV",
            "01ARZ3NDEKTSV4RRFFQ69G5FAW",
            "01ARZ3NDEKTSV4RRFFQ69G5FAX"
        ]
        
        with patch('pool.ClaudeClient') as MockClient:
            mock_instances = []
            for _ in session_ulids:
                mi = AsyncMock()
                mi.__aenter__ = AsyncMock(return_value=mi)
                mi.__aexit__ = AsyncMock(return_value=None)
                mock_instances.append(mi)
            MockClient.side_effect = mock_instances
            
            results = await asyncio.gather(*[
                pool.get_client(sid, client_config) for sid in session_ulids
            ])
            
            # Should create 3 different clients
            assert MockClient.call_count == 3
            assert len(pool._pool) == 3

    @pytest.mark.asyncio
    async def test_lock_per_session(self, pool, client_config):
        """Test that each session has its own lock."""
        session_ulid_1 = "01ARZ3NDEKTSV4RRFFQ69G5FAV"
        session_ulid_2 = "01ARZ3NDEKTSV4RRFFQ69G5FAW"
        
        with patch('pool.ClaudeClient') as MockClient:
            mock_instance = AsyncMock()
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_instance
            
            await pool.get_client(session_ulid_1, client_config)
            await pool.get_client(session_ulid_2, client_config)
            
            # Each session should have its own lock
            assert session_ulid_1 in pool._locks
            assert session_ulid_2 in pool._locks
            assert pool._locks[session_ulid_1] is not pool._locks[session_ulid_2]


# =============================================================================
# Pool Statistics Tests
# =============================================================================

class TestPoolStatistics:
    """Tests for pool statistics methods."""

    @pytest.mark.asyncio
    async def test_pool_size(self, pool, client_config):
        """Test pool_size returns correct count."""
        assert pool.pool_size() == 0
        
        with patch('pool.ClaudeClient') as MockClient:
            mock_instance = AsyncMock()
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_instance
            
            await pool.get_client("01ARZ3NDEKTSV4RRFFQ69G5FAV", client_config)
            assert pool.pool_size() == 1
            
            await pool.get_client("01ARZ3NDEKTSV4RRFFQ69G5FAW", client_config)
            assert pool.pool_size() == 2

    @pytest.mark.asyncio
    async def test_active_count(self, pool, client_config):
        """Test active_count returns correct count of in-use clients."""
        with patch('pool.ClaudeClient') as MockClient:
            mock_instance = AsyncMock()
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_instance
            
            await pool.get_client("01ARZ3NDEKTSV4RRFFQ69G5FAV", client_config)
            await pool.get_client("01ARZ3NDEKTSV4RRFFQ69G5FAW", client_config)
            await pool.release_client("01ARZ3NDEKTSV4RRFFQ69G5FAW")
            
            assert pool.active_count() == 1


# =============================================================================
# Context Manager Support Tests
# =============================================================================

class TestAsyncContextManager:
    """Tests for async context manager usage."""

    @pytest.mark.asyncio
    async def test_pool_as_context_manager(self, client_config):
        """Test pool can be used as async context manager."""
        with patch('pool.ClaudeClient') as MockClient:
            mock_instance = AsyncMock()
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_instance
            
            async with ClaudeClientPool() as pool:
                await pool.get_client("01ARZ3NDEKTSV4RRFFQ69G5FAV", client_config)
                assert pool.pool_size() == 1
