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


@pytest.fixture
def config_with_interpolation(temp_config_dir):
    """Create config file with variable interpolation."""
    config_path = temp_config_dir / "application.yml"
    config_content = """server:
  host: "${SERVER_HOST:0.0.0.0}"
  port: ${SERVER_PORT:8000}
  cors:
    origins:
      - "${CORS_ORIGIN:http://localhost:3000}"
    allow_credentials: true
    allow_methods:
      - "*"
    allow_headers:
      - "*"

database:
  url: "${DATABASE_URL:sqlite+aiosqlite:///app.db}"
  echo: ${DB_ECHO:false}
"""
    config_path.write_text(config_content)
    return config_path


@pytest.fixture
def invalid_yaml_file(temp_config_dir):
    """Create invalid YAML file for error testing."""
    config_path = temp_config_dir / "application.yml"
    config_content = """server:
  host: "0.0.0.0"
  port: 8000
  invalid: [unclosed bracket
"""
    config_path.write_text(config_content)
    return config_path


# =============================================================================
# TestYAMLLoading
# =============================================================================

class TestYAMLLoading:
    """Tests for YAML configuration loading."""

    def test_load_simple_yaml(self, sample_config_file, reset_cache):
        """Test that simple YAML file is loaded correctly."""
        from config import get_config, reset_config_cache

        data = get_config()  # sample_config_file)
        assert data is not None
        assert "server" in data
        assert "database" in data

    def test_load_nested_yaml(self, sample_config_file, reset_cache):
        """Test that nested YAML structure is loaded correctly."""
        from config import get_config, reset_config_cache

        data = get_config()  # sample_config_file)
        assert data["server"]["host"] == "0.0.0.0"
        assert data["server"]["port"] == 8000
        assert data["server"]["cors"]["origins"] == ["http://localhost:3000"]
        assert data["database"]["url"] == "sqlite+aiosqlite:///app.db"

    def test_missing_config_file_raises(self, temp_config_dir, reset_cache):
        """Test that FileNotFoundError is raised when config file doesn't exist."""
        from config import get_config, reset_config_cache

        missing_path = temp_config_dir / "nonexistent.yml"
        with pytest.raises(FileNotFoundError):
            get_config()  # missing_path)

    def test_invalid_yaml_raises(self, invalid_yaml_file, reset_cache):
        """Test that YAML parsing error is raised for malformed YAML."""
        from config import get_config, reset_config_cache

        with pytest.raises(Exception):  # yaml.YAMLError or similar
            get_config()  # invalid_yaml_file)


# =============================================================================
# TestVariableInterpolation
# =============================================================================

class TestVariableInterpolation:
    """Tests for variable interpolation in YAML values."""

    def test_env_var_interpolation(self, config_with_interpolation, monkeypatch, reset_cache):
        """Test that ${VAR} is replaced with environment variable value."""
        from config import get_config, reset_config_cache

        monkeypatch.setenv("SERVER_HOST", "192.168.1.1")
        monkeypatch.setenv("SERVER_PORT", "9000")

        data = get_config()  # config_with_interpolation)
        assert data["server"]["host"] == "192.168.1.1"
        assert data["server"]["port"] == "9000"

    def test_env_var_with_default(self, config_with_interpolation, monkeypatch, reset_cache):
        """Test that ${VAR:default} uses default when VAR is not set."""
        from config import get_config, reset_config_cache

        # Ensure env var is not set
        monkeypatch.delenv("CORS_ORIGIN", raising=False)

        data = get_config()  # config_with_interpolation)
        assert data["server"]["cors"]["origins"] == ["http://localhost:3000"]

    def test_missing_env_var_with_default(self, config_with_interpolation, reset_cache):
        """Test that ${MISSING:default_value} returns 'default_value'."""
        from config import get_config, reset_config_cache

        data = get_config()  # config_with_interpolation)
        assert data["server"]["host"] == "0.0.0.0"
        assert data["server"]["port"] == "8000"
        assert data["database"]["url"] == "sqlite+aiosqlite:///app.db"

    def test_nested_interpolation(self, config_with_interpolation, monkeypatch, reset_cache):
        """Test that interpolation works in nested values."""
        from config import get_config, reset_config_cache

        monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost/db")

        data = get_config()  # config_with_interpolation)
        assert data["database"]["url"] == "postgresql://user:pass@localhost/db"

    def test_interpolation_in_list(self, config_with_interpolation, monkeypatch, reset_cache):
        """Test that interpolation works inside list items."""
        from config import get_config, reset_config_cache

        monkeypatch.setenv("CORS_ORIGIN", "http://example.com")

        data = get_config()  # config_with_interpolation)
        assert data["server"]["cors"]["origins"] == ["http://example.com"]


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

    def test_override_creates_missing_key(self, sample_config_file, monkeypatch, reset_cache):
        """Test that override can set values not in YAML."""
        from config import get_config

        monkeypatch.setenv("APP_CONFIG_PATH", str(sample_config_file))
        monkeypatch.setenv("DATABASE__POOL_SIZE", "10")

        config = get_config()
        # Should add pool_size to database config
        assert hasattr(config.database, "pool_size")
        assert config.database.pool_size == 10


# =============================================================================
# TestProfileSupport
# =============================================================================

class TestProfileSupport:
    """Tests for profile-based configuration loading."""

    def test_default_profile_no_env(self, sample_config_file, monkeypatch, reset_cache):
        """Test that application.yml is loaded when APP_PROFILE is not set."""
        from config import get_config

        monkeypatch.setenv("APP_CONFIG_PATH", str(sample_config_file))
        monkeypatch.delenv("APP_PROFILE", raising=False)

        config = get_config()
        assert config.server.port == 8000
        assert config.database.url == "sqlite+aiosqlite:///app.db"

    def test_dev_profile(self, sample_config_file, sample_dev_config_file, monkeypatch, reset_cache):
        """Test that application-dev.yml is loaded when APP_PROFILE=dev."""
        from config import get_config

        monkeypatch.setenv("APP_CONFIG_PATH", str(sample_config_file))
        monkeypatch.setenv("APP_PROFILE", "dev")

        config = get_config()
        assert config.server.port == 9000
        assert config.server.host == "127.0.0.1"
        assert config.database.echo is True

    def test_missing_profile_file_raises(self, sample_config_file, monkeypatch, reset_cache):
        """Test that error is raised when profile file doesn't exist."""
        from config import get_config

        monkeypatch.setenv("APP_CONFIG_PATH", str(sample_config_file))
        monkeypatch.setenv("APP_PROFILE", "prod")

        with pytest.raises(FileNotFoundError):
            get_config()


# =============================================================================
# TestConfigPath
# =============================================================================

class TestConfigPath:
    """Tests for configuration path resolution."""

    def test_default_path(self, monkeypatch, reset_cache):
        """Test that server/application.yml is used by default."""
        from config import get_config

        monkeypatch.delenv("APP_CONFIG_PATH", raising=False)

        # Should try to load from default path
        # This will fail if file doesn't exist, which is expected
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

    def test_full_config_load(self, config_with_interpolation, monkeypatch, reset_cache):
        """Test loading complete config with all features enabled."""
        from config import get_config

        monkeypatch.setenv("APP_CONFIG_PATH", str(config_with_interpolation))
        monkeypatch.setenv("SERVER__PORT", "8888")
        monkeypatch.setenv("DATABASE__ECHO", "true")

        config = get_config()

        assert config.server.host == "0.0.0.0"  # default from interpolation
        assert config.server.port == 8888  # override from env
        assert config.database.echo is True  # override from env
        assert config.server.cors.origins == ["http://localhost:3000"]

    def test_config_reset_cache(self, sample_config_file, monkeypatch):
        """Test that reset_config_cache() clears singleton instance."""
        from config import get_config, reset_config_cache

        monkeypatch.setenv("APP_CONFIG_PATH", str(sample_config_file))

        config1 = get_config()
        reset_config_cache()
        config2 = get_config()

        assert config1 is not config2
        assert config1.server.port == config2.server.port
