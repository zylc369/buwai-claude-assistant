#!/usr/bin/env python3
"""Unit tests for main.py functions."""

import io
import pytest
from unittest.mock import patch

# Import functions to test
import main
from main import parse_args, process_message, process_messages


# =============================================================================
# Mock Classes for TextBlock and ToolUseBlock
# =============================================================================

class MockTextBlock:
    """Mock TextBlock class for testing."""
    def __init__(self, text: str):
        self.text = text


class MockToolUseBlock:
    """Mock ToolUseBlock class for testing."""
    def __init__(self, id: str, name: str, input: dict):
        self.id = id
        self.name = name
        self.input = input


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def mock_text_block():
    """Create a mock TextBlock for testing."""
    return MockTextBlock("Hello, this is a test message.")


@pytest.fixture
def mock_tool_use_block():
    """Create a mock ToolUseBlock for testing."""
    return MockToolUseBlock(
        id="tool_123",
        name="read_file",
        input={"path": "/tmp/test.txt"}
    )


# =============================================================================
# parse_args() Tests
# =============================================================================

class TestParseArgs:
    """Tests for parse_args() function."""

    def test_default_values(self):
        """Test that default values are stream=True and verbose=True."""
        with patch('sys.argv', ['main.py', '--cwd', '/tmp/test']):
            args = parse_args()
            assert args.stream is True
            assert args.verbose is True
            assert args.cwd == '/tmp/test'

    def test_no_stream_flag(self):
        """Test --no-stream sets stream=False."""
        with patch('sys.argv', ['main.py', '--cwd', '/tmp/test', '--no-stream']):
            args = parse_args()
            assert args.stream is False
            assert args.verbose is True  # verbose should remain default

    def test_quiet_flag(self):
        """Test --quiet sets verbose=False."""
        with patch('sys.argv', ['main.py', '--cwd', '/tmp/test', '--quiet']):
            args = parse_args()
            assert args.stream is True  # stream should remain default
            assert args.verbose is False

    def test_combined_no_stream_and_quiet(self):
        """Test combination of --no-stream and --quiet flags."""
        with patch('sys.argv', ['main.py', '--cwd', '/tmp/test', '--no-stream', '--quiet']):
            args = parse_args()
            assert args.stream is False
            assert args.verbose is False

    def test_explicit_stream_and_verbose(self):
        """Test explicit --stream and --verbose flags."""
        with patch('sys.argv', ['main.py', '--cwd', '/tmp/test', '--stream', '--verbose']):
            args = parse_args()
            assert args.stream is True
            assert args.verbose is True

    def test_cwd_required(self):
        """Test that --cwd is required."""
        with patch('sys.argv', ['main.py']):
            with pytest.raises(SystemExit):
                parse_args()

    def test_settings_default_value(self):
        """Test that --settings has correct default."""
        with patch('sys.argv', ['main.py', '--cwd', '/tmp/test']):
            args = parse_args()
            # Default should be expanded from ~/.claude/settings.json
            assert args.settings.endswith('.claude/settings.json')

    def test_settings_explicit_path(self):
        """Test explicit --settings path."""
        with patch('sys.argv', ['main.py', '--cwd', '/tmp/test', '--settings', '/custom/settings.json']):
            args = parse_args()
            assert args.settings == '/custom/settings.json'

    def test_settings_expanded_path(self):
        """Test that ~ in settings path is expanded."""
        with patch('sys.argv', ['main.py', '--cwd', '/tmp/test', '--settings', '~/my-settings.json']):
            args = parse_args()
            # ~ should be expanded to home directory
            assert '~' not in args.settings
            assert args.settings.endswith('/my-settings.json')


# =============================================================================
# process_message() Tests - TextBlock
# =============================================================================

class TestProcessMessageTextBlock:
    """Tests for process_message() with TextBlock."""

    def test_text_block_streaming_mode(self, mock_text_block):
        """Test TextBlock in streaming mode prints and returns empty string."""
        captured = io.StringIO()
        with patch('sys.stdout', captured):
            with patch.object(main, 'TextBlock', MockTextBlock):
                with patch.object(main, 'ToolUseBlock', MockToolUseBlock):
                    result = process_message(mock_text_block, stream=True, verbose=True)
        
        assert result == ""
        assert "Hello, this is a test message." in captured.getvalue()

    def test_text_block_non_streaming_mode(self, mock_text_block):
        """Test TextBlock in non-streaming mode returns text without printing."""
        with patch.object(main, 'TextBlock', MockTextBlock):
            with patch.object(main, 'ToolUseBlock', MockToolUseBlock):
                with patch('sys.stdout') as mock_stdout:
                    result = process_message(mock_text_block, stream=False, verbose=True)
        
        assert result == "Hello, this is a test message."
        # Should not print in non-streaming mode
        mock_stdout.write.assert_not_called()


# =============================================================================
# process_message() Tests - ToolUseBlock
# =============================================================================

class TestProcessMessageToolUseBlock:
    """Tests for process_message() with ToolUseBlock."""

    def test_tool_use_block_verbose_true_streaming(self, mock_tool_use_block):
        """Test ToolUseBlock with verbose=True in streaming mode shows tool info."""
        captured = io.StringIO()
        with patch('sys.stdout', captured):
            with patch.object(main, 'TextBlock', MockTextBlock):
                with patch.object(main, 'ToolUseBlock', MockToolUseBlock):
                    result = process_message(mock_tool_use_block, stream=True, verbose=True)
        
        output = captured.getvalue()
        assert "[Tool: read_file]" in output
        assert "Input: {'path': '/tmp/test.txt'}" in output

    def test_tool_use_block_verbose_true_non_streaming(self, mock_tool_use_block):
        """Test ToolUseBlock with verbose=True in non-streaming mode returns tool info."""
        with patch.object(main, 'TextBlock', MockTextBlock):
            with patch.object(main, 'ToolUseBlock', MockToolUseBlock):
                result = process_message(mock_tool_use_block, stream=False, verbose=True)
        
        assert "[Tool: read_file]" in result
        assert "Input: {'path': '/tmp/test.txt'}" in result

    def test_tool_use_block_verbose_false(self, mock_tool_use_block):
        """Test ToolUseBlock with verbose=False returns empty string."""
        with patch.object(main, 'TextBlock', MockTextBlock):
            with patch.object(main, 'ToolUseBlock', MockToolUseBlock):
                result = process_message(mock_tool_use_block, stream=True, verbose=False)
        assert result == ""


# =============================================================================
# process_message() Tests - Unknown Types
# =============================================================================

class TestProcessMessageUnknownType:
    """Tests for process_message() with unknown message types."""

    def test_unknown_type_verbose_true(self):
        """Test unknown type logs to stderr when verbose=True."""
        captured = io.StringIO()
        with patch('sys.stderr', captured):
            with patch.object(main, 'TextBlock', MockTextBlock):
                with patch.object(main, 'ToolUseBlock', MockToolUseBlock):
                    unknown_block = {"some": "dict"}
                    result = process_message(unknown_block, stream=True, verbose=True)
        
        assert "[Unknown message type:" in captured.getvalue()

    def test_unknown_type_verbose_false(self):
        """Test unknown type is silent when verbose=False."""
        with patch.object(main, 'TextBlock', MockTextBlock):
            with patch.object(main, 'ToolUseBlock', MockToolUseBlock):
                with patch('sys.stderr') as mock_stderr:
                    unknown_block = {"some": "dict"}
                    result = process_message(unknown_block, stream=True, verbose=False)
        
        assert result == ""
        # Should not write to stderr
        mock_stderr.write.assert_not_called()


# =============================================================================
# process_messages() Tests
# =============================================================================

class TestProcessMessages:
    """Tests for process_messages() function."""

    def test_process_messages_multiple_blocks(self, mock_text_block, mock_tool_use_block):
        """Test process_messages aggregates multiple blocks correctly."""
        with patch.object(main, 'TextBlock', MockTextBlock):
            with patch.object(main, 'ToolUseBlock', MockToolUseBlock):
                blocks = [mock_text_block, mock_tool_use_block]
                result = process_messages(blocks, verbose=True)
        
        assert "Hello, this is a test message." in result
        assert "[Tool: read_file]" in result

    def test_process_messages_empty_list(self):
        """Test process_messages with empty list returns empty string."""
        with patch.object(main, 'TextBlock', MockTextBlock):
            with patch.object(main, 'ToolUseBlock', MockToolUseBlock):
                result = process_messages([], verbose=True)
        assert result == ""

    def test_process_messages_verbose_false(self, mock_text_block, mock_tool_use_block):
        """Test process_messages with verbose=False hides tool info."""
        with patch.object(main, 'TextBlock', MockTextBlock):
            with patch.object(main, 'ToolUseBlock', MockToolUseBlock):
                blocks = [mock_text_block, mock_tool_use_block]
                result = process_messages(blocks, verbose=False)
        
        assert "Hello, this is a test message." in result
        assert "[Tool:" not in result


# =============================================================================
# Integration Tests
# =============================================================================

class TestIntegration:
    """Integration tests combining multiple functions."""

    def test_parse_args_and_process_message_workflow(self, mock_text_block):
        """Test workflow: parse args then process a message."""
        with patch('sys.argv', ['main.py', '--cwd', '/tmp/test', '--no-stream', '--quiet']):
            args = parse_args()
            
            with patch.object(main, 'TextBlock', MockTextBlock):
                with patch.object(main, 'ToolUseBlock', MockToolUseBlock):
                    # Use parsed args to control process_message
                    result = process_message(mock_text_block, stream=args.stream, verbose=args.verbose)
        
        assert args.stream is False
        assert args.verbose is False
        assert result == "Hello, this is a test message."
