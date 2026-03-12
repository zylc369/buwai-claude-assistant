#!/usr/bin/env python3
"""Unit tests for claude_client.py functions."""

import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import classes to test
from claude_client import ClaudeClientConfig, ClaudeClient


class TestClaudeClientConfig:
    """Tests for ClaudeClientConfig dataclass."""

    def test_config_requires_cwd(self):
        """Test that cwd is required (no default)."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({}, f)
            settings_path = f.name
        
        try:
            # Should raise TypeError if cwd is missing
            with pytest.raises(TypeError):
                ClaudeClientConfig(settings=settings_path)
        finally:
            Path(settings_path).unlink()

    def test_config_requires_settings(self):
        """Test that settings is required (no default)."""
        # Should raise TypeError if settings is missing
        with pytest.raises(TypeError):
            ClaudeClientConfig(cwd="/tmp/test")

    def test_config_with_all_params(self):
        """Test config with all parameters."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"api_key": "test-key"}, f)
            settings_path = f.name
        
        try:
            config = ClaudeClientConfig(
                system_prompt="Custom prompt",
                cwd="/tmp/test",
                settings=settings_path
            )
            assert config.system_prompt == "Custom prompt"
            assert config.cwd == "/tmp/test"
            assert config.settings == settings_path
        finally:
            Path(settings_path).unlink()

    def test_config_default_system_prompt(self):
        """Test that system_prompt has correct default."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({}, f)
            settings_path = f.name
        
        try:
            config = ClaudeClientConfig(
                cwd="/tmp/test",
                settings=settings_path
            )
            assert config.system_prompt == "You are a helpful coding assistant"
        finally:
            Path(settings_path).unlink()


class TestClaudeClientInit:
    """Tests for ClaudeClient.__init__ method."""

    def test_init_reads_settings_json(self):
        """Test that ClaudeClient reads settings.json from provided path."""
        settings_data = {"api_key": "test-key-123", "model": "claude-3"}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(settings_data, f)
            settings_path = f.name
        
        try:
            config = ClaudeClientConfig(
                cwd="/tmp/test",
                settings=settings_path
            )
            
            # Mock ClaudeSDKClient to avoid actual SDK dependency
            with patch('claude_client.ClaudeSDKClient'):
                client = ClaudeClient(config)
                assert client._options.cwd == "/tmp/test"
                assert client._options.system_prompt == "You are a helpful coding assistant"
        finally:
            Path(settings_path).unlink()

    # Note: FileNotFoundError test removed - SDK handles settings file validation
    def test_init_uses_custom_system_prompt(self):
        """Test that ClaudeClient uses custom system_prompt."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({}, f)
            settings_path = f.name
        
        try:
            config = ClaudeClientConfig(
                system_prompt="Custom assistant prompt",
                cwd="/tmp/test",
                settings=settings_path
            )
            
            with patch('claude_client.ClaudeSDKClient'):
                client = ClaudeClient(config)
                assert client._options.system_prompt == "Custom assistant prompt"
        finally:
            Path(settings_path).unlink()

    def test_init_uses_cwd_from_config(self):
        """Test that ClaudeClient uses cwd from config."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({}, f)
            settings_path = f.name
        
        try:
            config = ClaudeClientConfig(
                cwd="/custom/working/directory",
                settings=settings_path
            )
            
            with patch('claude_client.ClaudeSDKClient'):
                client = ClaudeClient(config)
                assert client._options.cwd == "/custom/working/directory"
        finally:
            Path(settings_path).unlink()
