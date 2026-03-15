#!/usr/bin/env python3
"""Unit tests for configuration system with YAML loading, variable interpolation, and profile support."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from pydantic import BaseModel, Field, ValidationError


# =============================================================================
# Pydantic Models for Testing (mirror of actual config models)
# =============================================================================

class CorsConfig(BaseModel):
    """CORS configuration model."""
    origins: list[str]
    allow_credentials: bool = True
    allow_methods: list[str] = ["*"]
    allow_headers: list[str] = ["*"]


class ServerConfig(BaseModel):
    """Server configuration model."""
    host: str = "0.0.0.0"
    port: int = Field(default=8000, ge=1, le=65535)
    cors: CorsConfig


class DatabaseConfig(BaseModel):
    """Database configuration model."""
    url: str
    echo: bool = False


class AppConfig(BaseModel):
    """Application configuration model."""
    server: ServerConfig
    database: DatabaseConfig


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def reset_cache():
    """Reset config cache between tests."""
    from config import reset_config_cache as actual_reset
    actual_reset()
    yield
    actual_reset()


@pytest.fixture
def temp_config_dir():
    """Create temporary directory for config files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_config_file(temp_config_dir):
    """Create a sample application.yml config file."""
    config_path = temp_config_dir / "application.yml"
    config_content = """server:
  host: "0.0.0.0"
  port: 8000
  cors:
    origins:
      - "http://localhost:3000"
    allow_credentials: true
    allow_methods:
      - "*"
    allow_headers:
      - "*"

database:
  url: "sqlite+aiosqlite:///app.db"
  echo: false
"""
    config_path.write_text(config_content)
    return config_path


@pytest.fixture
def sample_dev_config_file(temp_config_dir):
    """Create a sample application-dev.yml config file."""
    config_path = temp_config_dir / "application-dev.yml"
    config_content = """server:
  host: "127.0.0.1"
  port: 9000
  cors:
    origins:
      - "http://localhost:3000"
      - "http://localhost:5173"
    allow_credentials: true
    allow_methods:
      - "*"
    allow_headers:
      - "*"

database:
  url: "sqlite+aiosqlite:///dev.db"
  echo: true
"""
    config_path.write_text(config_content)
    return config_path


# =============================================================================
# TestEnvironmentOverrides
# =============================================================================

class TestEnvironmentOverrides:
    """Tests for environment variable overrides with __ separator."""

    def test_flat_override(self, sample_config_file, monkeypatch, reset_cache):
        """Test that SERVER__PORT=9000 overrides server.port."""
        from config import get_config

        monkeypatch.setenv("APP_CONFIG_PATH", str(sample_config_file))
        monkeypatch.setenv("SERVER__PORT", "9000")

        config = get_config()
        assert config.server.port == 9000

    def test_nested_override(self, sample_config_file, monkeypatch, reset_cache):
        """Test that SERVER__CORS__ORIGINS overrides server.cors.origins."""
        from config import get_config

        monkeypatch.setenv("APP_CONFIG_PATH", str(sample_config_file))
        monkeypatch.setenv("SERVER__CORS__ORIGINS", '["http://example.com"]')

        config = get_config()
        assert config.server.cors.origins == ["http://example.com"]

    def test_override_takes_precedence(self, sample_config_file, monkeypatch, reset_cache):
        """Test that environment override beats YAML value."""
        from config import get_config

        monkeypatch.setenv("APP_CONFIG_PATH", str(sample_config_file))
        monkeypatch.setenv("SERVER__HOST", "192.168.1.100")

        config = get_config()
        assert config.server.host == "192.168.1.100"

# =============================================================================
# TestProfileSupport
# =============================================================================

class TestProfileSupport:

    def test_default_profile_no_env(self, sample_config_file, monkeypatch, reset_cache):
        from config import get_config

        monkeypatch.setenv("APP_CONFIG_PATH", str(sample_config_file))
        monkeypatch.delenv("APP_PROFILE", raising=False)

        config = get_config()
        assert config.server.port == 8000
        assert config.database.url == "sqlite+aiosqlite:///app.db"

    def test_dev_profile(self, sample_config_file, sample_dev_config_file, monkeypatch, reset_cache, temp_config_dir):
        from config import get_config, get_config_path

        monkeypatch.delenv("APP_CONFIG_PATH", raising=False)
        monkeypatch.setenv("APP_PROFILE", "dev")

        monkeypatch.setattr("config.get_config_path", lambda: sample_dev_config_file)

        config = get_config()
        assert config.server.port == 9000
        assert config.server.host == "127.0.0.1"
        assert config.database.echo is True

    def test_missing_profile_file_raises(self, temp_config_dir, monkeypatch, reset_cache):
        from config import get_config

        monkeypatch.delenv("APP_CONFIG_PATH", raising=False)
        monkeypatch.setenv("APP_PROFILE", "nonexistent")

        with pytest.raises(FileNotFoundError):
            get_config()


# =============================================================================
# TestConfigPath
# =============================================================================

class TestConfigPath:
    """Tests for configuration path resolution."""

    def test_default_path(self, monkeypatch, reset_cache):
        from config import get_config, get_config_path

        monkeypatch.delenv("APP_CONFIG_PATH", raising=False)
        monkeypatch.delenv("APP_PROFILE", raising=False)

        path = get_config_path()
        assert path.name == "application.yml"

    def test_default_path_missing_file(self, monkeypatch, reset_cache, temp_config_dir):
        from config import get_config

        non_existent_path = temp_config_dir / "nonexistent" / "application.yml"
        monkeypatch.delenv("APP_CONFIG_PATH", raising=False)
        monkeypatch.delenv("APP_PROFILE", raising=False)
        monkeypatch.setattr("config.get_config_path", lambda: non_existent_path)

        with pytest.raises(FileNotFoundError):
            get_config()

    def test_custom_path_via_env_var(self, sample_config_file, monkeypatch, reset_cache):
        """Test that APP_CONFIG_PATH is used when set."""
        from config import get_config

        monkeypatch.setenv("APP_CONFIG_PATH", str(sample_config_file))

        config = get_config()
        assert config is not None
        assert config.server.port == 8000

    def test_missing_config_file_raises_file_not_found(self, temp_config_dir, monkeypatch, reset_cache):
        """Test that clear error message is given when config file doesn't exist."""
        from config import get_config

        missing_path = temp_config_dir / "missing.yml"
        monkeypatch.setenv("APP_CONFIG_PATH", str(missing_path))

        with pytest.raises(FileNotFoundError) as exc_info:
            get_config()

        assert "missing.yml" in str(exc_info.value)


# =============================================================================
# TestConfigModels
# =============================================================================

class TestConfigModels:
    """Tests for Pydantic configuration model validation."""

    def test_server_config_default_values(self):
        """Test that ServerConfig has correct default values."""
        cors = CorsConfig(origins=["http://localhost:3000"])
        config = ServerConfig(cors=cors)

        assert config.host == "0.0.0.0"
        assert config.port == 8000

    def test_server_config_port_validation(self):
        """Test that port must be between 1 and 65535."""
        cors = CorsConfig(origins=["http://localhost:3000"])

        # Valid ports
        ServerConfig(cors=cors, port=1)
        ServerConfig(cors=cors, port=65535)

        # Invalid ports
        with pytest.raises(ValidationError):
            ServerConfig(cors=cors, port=0)

        with pytest.raises(ValidationError):
            ServerConfig(cors=cors, port=65536)

    def test_database_config_url_required(self):
        """Test that database URL is required."""
        with pytest.raises(ValidationError):
            DatabaseConfig()

        # Valid with URL
        config = DatabaseConfig(url="sqlite:///test.db")
        assert config.url == "sqlite:///test.db"

    def test_app_config_singleton(self, sample_config_file, monkeypatch, reset_cache):
        """Test that get_config() returns cached singleton instance."""
        from config import get_config

        monkeypatch.setenv("APP_CONFIG_PATH", str(sample_config_file))

        config1 = get_config()
        config2 = get_config()

        assert config1 is config2


# =============================================================================
# TestConfigIntegration
# =============================================================================

class TestConfigIntegration:
    """Integration tests for complete configuration system."""

    def test_config_reset_cache(self, sample_config_file, monkeypatch):
        """Test that reset_config_cache() clears singleton instance."""
        from config import get_config, reset_config_cache

        monkeypatch.setenv("APP_CONFIG_PATH", str(sample_config_file))

        config1 = get_config()
        reset_config_cache()
        config2 = get_config()

        assert config1 is not config2
        assert config1.server.port == config2.server.port
