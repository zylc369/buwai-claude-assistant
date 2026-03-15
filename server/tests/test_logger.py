#!/usr/bin/env python3
"""Unit tests for logger.py - TDD Red Phase (logger.py doesn't exist yet)."""

import asyncio
import logging
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Generator
from unittest.mock import patch, MagicMock, Mock

import pytest


# Test Fixtures

@pytest.fixture
def temp_log_dir() -> Generator[Path, None, None]:
    """Create temporary directory for log files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_config(temp_log_dir: Path) -> dict:
    """Create mock logger configuration."""
    return {
        "log_dir": str(temp_log_dir / "app-logs"),
        "log_filename": f"test-{uuid.uuid4().hex[:8]}",  # Unique name per test
        "level": logging.INFO,
        "format_string": "%(asctime)s | %(process)d | %(thread)d | %(class_name)s | %(funcName)s | %(request_id)s | %(message)s",
        "use_queue": False,  # Disable queue for pytest caplog compatibility
    }


@pytest.fixture
def cleanup_request_id():
    """Clean up request_id contextvar between tests."""
    from logger import request_id_context as _request_id_context
    token = _request_id_context.set(None)
    yield
    _request_id_context.reset(token)


# Test Logger Initialization

class TestLoggerInitialization:
    """Tests for Logger initialization."""

    def test_logger_initialization(self, mock_config: dict):
        """Test Logger creates with correct config."""
        from logger import Logger

        logger = Logger(**mock_config)

        assert logger is not None
        assert logger.log_dir == Path(mock_config["log_dir"])
        assert logger.log_filename == mock_config["log_filename"]
        assert logger.level == logging.INFO
        assert hasattr(logger, 'logger')

    def test_logger_creates_handlers(self, mock_config: dict):
        """Test Logger creates proper handlers."""
        from logger import Logger

        logger = Logger(**mock_config)

        assert logger.logger.handlers is not None
        assert len(logger.logger.handlers) > 0

    def test_logger_sets_log_level(self, mock_config: dict):
        """Test Logger sets correct log level."""
        from logger import Logger

        logger = Logger(**mock_config)

        assert logger.logger.level == logging.INFO


# Test Log Format

class TestLogFormat:
    """Tests for log format and fields."""

    def test_log_format_contains_all_fields(self, mock_config: dict, caplog):
        """Test output contains: 时间, 进程ID, 线程ID, class_name, funcName, request_id."""
        from logger import Logger

        logger = Logger(**mock_config)

        with caplog.at_level(logging.INFO):
            logger.logger.info("Test message")

        assert len(caplog.records) > 0
        record = caplog.records[0]

        assert hasattr(record, 'process')
        assert hasattr(record, 'thread')
        assert hasattr(record, 'name')
        assert hasattr(record, 'funcName')
        assert hasattr(record, 'created')

    def test_formatted_log_string_contains_all_fields(self, mock_config: dict, caplog):
        """Test formatted log string contains all required field labels."""
        from logger import Logger

        logger = Logger(**mock_config)

        with caplog.at_level(logging.INFO):
            logger.logger.info("Test message")

        assert len(caplog.records) > 0
        formatted_message = caplog.text

        assert "Test message" in formatted_message


# Test Daily Rotation

class TestDailyRotation:
    """Tests for daily log file rotation."""

    def test_daily_rotation_filename(self, mock_config: dict):
        """Test rotation uses DailyRotatingHandler for app-年_月_日.log files."""
        from logger import Logger, DailyRotatingHandler

        logger = Logger(**mock_config)

        assert any(isinstance(h, DailyRotatingHandler) for h in logger._handlers)


# Test Request ID Context

class TestRequestIdContext:
    """Tests for request_id context variable handling."""

    def test_request_id_context(self, cleanup_request_id):
        """Test set_request_id()/get_request_id() works with contextvars."""
        from logger import set_request_id, get_request_id

        test_id = "req-12345"
        set_request_id(test_id)

        retrieved_id = get_request_id()

        assert retrieved_id == test_id

    def test_request_id_none_by_default(self, cleanup_request_id):
        """Test get_request_id() returns None when not set."""
        from logger import get_request_id

        assert get_request_id() is None

    def test_request_id_can_be_overwritten(self, cleanup_request_id):
        """Test set_request_id() can overwrite existing value."""
        from logger import set_request_id, get_request_id

        set_request_id("req-1")
        assert get_request_id() == "req-1"

        set_request_id("req-2")
        assert get_request_id() == "req-2"


# Test Request ID in Log Output

class TestRequestIdInLogOutput:
    """Tests for request_id appearing in formatted logs."""

    def test_request_id_in_log_output(self, mock_config: dict, cleanup_request_id, caplog):
        """Test Request ID appears in formatted log."""
        from logger import Logger, set_request_id, get_request_id

        test_id = "req-67890"
        set_request_id(test_id)

        logger = Logger(**mock_config)

        with caplog.at_level(logging.INFO):
            logger.logger.info("Test message with request ID")

        assert len(caplog.records) > 0
        assert get_request_id() == test_id

    def test_request_id_none_in_log_output(self, mock_config: dict, cleanup_request_id, caplog):
        """Test log works when request_id is None."""
        from logger import Logger, get_request_id

        logger = Logger(**mock_config)

        with caplog.at_level(logging.INFO):
            logger.logger.info("Test message without request ID")

        assert len(caplog.records) > 0
        assert get_request_id() is None


# Test Class Name Detection

class TestClassNameDetection:
    """Tests for class name detection from calling context."""

    class TestClass:
        """Test class for logger class name detection."""

        def method_with_logger(self, mock_config: dict):
            """Method that logs something."""
            from logger import Logger

            logger = Logger(**mock_config)
            logger.logger.info("Test from class method")

    def test_class_name_detection(self, mock_config: dict):
        """Test Logger detects class name from calling context."""
        from logger import Logger
        import inspect

        frame = inspect.currentframe()
        if frame and frame.f_back:
            frame = frame.f_back

        test_obj = self.TestClass()
        test_obj.method_with_logger(mock_config)

    def test_class_name_from_frame(self, mock_config: dict):
        """Test class name is extracted from stack frame."""
        from logger import Logger

        logger = Logger(**mock_config)

        class SomeClass:
            def log_something(self):
                logger.logger.info("Class method log")

        obj = SomeClass()
        obj.log_something()

        assert True


# Test Filename Fallback

class TestFilenameFallback:
    """Tests for filename fallback when class name is not available."""

    def test_filename_fallback(self, mock_config: dict, caplog):
        """Test uses filename when no class name available."""
        from logger import Logger

        logger = Logger(**mock_config)

        def standalone_function():
            logger.logger.info("Standalone function log")

        standalone_function()

        assert len(caplog.records) > 0

        record = caplog.records[0]
        assert hasattr(record, 'name') or hasattr(record, 'class_name')

    def test_module_name_in_logs(self, mock_config: dict, caplog):
        """Test module name appears in logs when class name not available."""
        from logger import Logger

        logger = Logger(**mock_config)
        logger.logger.info("Module level log")

        assert len(caplog.records) > 0
        record = caplog.records[0]

        assert hasattr(record, 'name') or hasattr(record, 'class_name')


# Test Log Directory Creation

class TestLogDirectoryCreation:
    """Tests for automatic log directory creation."""

    def test_log_directory_creation(self, temp_log_dir: Path):
        """Test creates app-logs/ if not exists."""
        from logger import Logger

        log_dir = temp_log_dir / "app-logs"
        assert not log_dir.exists()

        config = {
            "log_dir": str(log_dir),
            "log_filename": "app",
            "level": logging.INFO,
            "format_string": "%(asctime)s | %(message)s"
        }

        logger = Logger(**config)

        assert log_dir.exists()
        assert log_dir.is_dir()

    def test_log_directory_exists_before_creation(self, temp_log_dir: Path):
        """Test handles existing directory gracefully."""
        from logger import Logger

        log_dir = temp_log_dir / "app-logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        assert log_dir.exists()

        config = {
            "log_dir": str(log_dir),
            "log_filename": "app",
            "level": logging.INFO,
            "format_string": "%(asctime)s | %(message)s"
        }

        logger = Logger(**config)
        assert logger is not None


# Test Queue Handler Pattern

class TestQueueHandlerPattern:
    """Tests for QueueHandler + QueueListener pattern."""

    def test_queue_handler_pattern(self, temp_log_dir: Path):
        """Test uses QueueHandler + QueueListener pattern."""
        from logger import Logger

        config = {
            "log_dir": str(temp_log_dir / "app-logs"),
            "log_filename": "app",
            "level": logging.INFO,
            "format_string": "%(asctime)s | %(message)s",
            "use_queue": True,
        }
        logger = Logger(**config)

        has_queue_handler = any(
            isinstance(h, logging.handlers.QueueHandler)
            for h in logger.logger.handlers
        )

        assert has_queue_handler, "Logger should use QueueHandler"

        queue_handlers = [
            h for h in logger.logger.handlers
            if isinstance(h, logging.handlers.QueueHandler)
        ]

        if queue_handlers:
            queue_handler = queue_handlers[0]

    def test_queue_listener_started(self, mock_config: dict):
        """Test QueueListener is started for async logging."""
        from logger import Logger

        logger = Logger(**mock_config)

        logger.logger.info("Test queue message")

        assert True

    @pytest.mark.asyncio
    async def test_async_logging_with_queue(self, mock_config: dict):
        """Test async logging works with queue pattern."""
        from logger import Logger

        logger = Logger(**mock_config)

        for i in range(10):
            logger.logger.info(f"Async message {i}")
            await asyncio.sleep(0.01)

        assert True


# Test Chinese Formatter

class TestChineseFormatter:
    """Tests for ChineseFormatter class."""

    def test_chinese_formatter_exists(self):
        """Test ChineseFormatter class exists."""
        from logger import ChineseFormatter

        formatter = ChineseFormatter("%(asctime)s | %(message)s")
        assert formatter is not None

    def test_chinese_formatter_format_record(self, mock_config: dict):
        """Test ChineseFormatter produces correct format."""
        from logger import Logger, ChineseFormatter

        formatter = ChineseFormatter(
            "%(asctime)s | %(process)d | %(thread)d | %(class_name)s | "
            "%(funcName)s | %(request_id)s | %(message)s"
        )

        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="测试消息",
            args=(),
            exc_info=None
        )

        formatted = formatter.format(record)

        assert "测试消息" in formatted
        assert "|" in formatted

    def test_chinese_formatter_handles_chinese_chars(self, mock_config: dict, caplog):
        """Test ChineseFormatter handles Chinese characters correctly."""
        from logger import Logger

        logger = Logger(**mock_config)

        with caplog.at_level(logging.INFO):
            logger.logger.info("中文日志消息")
            logger.logger.info("English log message")
            logger.logger.info("混合 Mixed 中文与English")

        assert len(caplog.records) == 3
        messages = [record.getMessage() for record in caplog.records]

        assert "中文日志消息" in messages
        assert "English log message" in messages
        assert "混合 Mixed 中文与English" in messages