"""Spring Boot-style YAML configuration loader.

This module provides a configuration system inspired by Spring Boot's
application.yml pattern, supporting:
- YAML-based configuration files
- Environment variable interpolation (${VAR:default})
- Environment variable overrides (APP__SECTION__KEY)
- Profile-specific configuration files
- Pydantic model validation
"""

import json
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

import yaml
from pydantic import BaseModel, Field, field_validator

from logger import get_logger

logger = get_logger(__name__)


# Environment variable pattern for ${VAR:default} interpolation
ENV_VAR_PATTERN = re.compile(r'\$\{([^}:]+)(?::([^}]*))?\}')

# Known config section prefixes for env var overrides
CONFIG_SECTIONS = {"SERVER", "DATABASE", "LOGGING", "PROJECTS"}


class CorsConfig(BaseModel):
    """CORS (Cross-Origin Resource Sharing) configuration.
    
    Attributes:
        origins: List of allowed origins for CORS requests.
        allow_credentials: Whether to allow credentials in CORS requests.
        allow_methods: List of allowed HTTP methods.
        allow_headers: List of allowed HTTP headers.
    """
    origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    allow_credentials: bool = True
    allow_methods: list[str] = Field(default_factory=lambda: ["*"])
    allow_headers: list[str] = Field(default_factory=lambda: ["*"])


class ServerConfig(BaseModel):
    """Server configuration settings.
    
    Attributes:
        host: Host address to bind the server to.
        port: Port number to listen on (1-65535).
        cors: CORS configuration for the server.
    """
    host: str = "0.0.0.0"
    port: int = Field(default=8000, ge=1, le=65535)
    cors: CorsConfig = Field(default_factory=CorsConfig)


class DatabaseConfig(BaseModel):
    """Database connection configuration.
    
    Attributes:
        url: Database connection URL (supports SQLAlchemy format).
        echo: Whether to echo SQL statements for debugging.
    """
    url: str = "sqlite+aiosqlite:///app.db"
    echo: bool = False
    
    @field_validator('url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate that database URL is not empty.
        
        Args:
            v: The database URL value to validate.
            
        Returns:
            The validated database URL.
            
        Raises:
            ValueError: If the URL is empty.
        """
        if not v:
            raise ValueError("Database URL cannot be empty")
        return v


class LoggingConfig(BaseModel):
    """日志配置设置。
    
    Attributes:
        enabled: 是否启用日志记录。
        level: 日志级别 (DEBUG/INFO/WARNING/ERROR/CRITICAL)。
        dir: 日志文件存储目录。
        format: 日志格式字符串。
        date_format: 日志日期格式字符串。
    """
    enabled: bool = True
    level: str = "INFO"
    dir: str = "app-logs"
    format: str = "[时间：%(asctime)s][进程ID:%(process)d][线程ID:%(thread)d][%(class_name)s][%(funcName)s][%(request_id)s] - %(message)s"
    date_format: str = "%Y-%m-%d %H-%M-%S"
    
    @field_validator('level')
    @classmethod
    def validate_level(cls, v: str) -> str:
        """验证日志级别是否有效。
        
        Args:
            v: 要验证的日志级别值。
            
        Returns:
            验证后的日志级别（大写形式）。
            
        Raises:
            ValueError: 如果日志级别无效。
        """
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return v.upper()


class ProjectsConfig(BaseModel):
    """Projects directory configuration.
    
    Attributes:
        root: Root directory for all projects (relative or absolute path).
    """
    root: str = "projectsRoot"
    
    @field_validator('root')
    @classmethod
    def validate_root(cls, v: str) -> str:
        """Validate that root path is not empty.
        
        Args:
            v: The root path value to validate.
            
        Returns:
            The validated root path.
            
        Raises:
            ValueError: If the root path is empty.
        """
        if not v or not v.strip():
            raise ValueError("Projects root path cannot be empty")
        return v.strip()


class AppConfig(BaseModel):
    """Root application configuration.
    
    This is the top-level configuration model that contains all
    configuration sections for the application.
    
    Attributes:
        server: Server-related configuration settings.
        database: Database connection configuration.
        logging: Logging configuration settings.
        projects: Projects directory configuration.
    """
    server: ServerConfig = Field(default_factory=ServerConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    projects: ProjectsConfig = Field(default_factory=ProjectsConfig)


def interpolate_env_vars(value: Any) -> Any:
    """Recursively interpolate ${VAR:default} patterns in configuration values.

    Supports environment variable substitution with optional default values:
    - ${VAR} - substitutes with env var VAR or empty string if not set
    - ${VAR:default} - substitutes with env var VAR or 'default' if not set

    Args:
        value: The value to process (can be str, dict, list, or any other type).

    Returns:
        The value with all environment variables interpolated.
    """
    logger.debug(f"Interpolating environment variables in value: {type(value).__name__}")
    if isinstance(value, str):
        def replace(match: re.Match[str]) -> str:
            var_name = match.group(1)
            default = match.group(2) if match.group(2) is not None else ""
            return os.getenv(var_name, default)
        result = ENV_VAR_PATTERN.sub(replace, value)
        if result != value:
            logger.debug(f"Interpolated {value} -> {result}")
        return result
    elif isinstance(value, dict):
        return {k: interpolate_env_vars(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [interpolate_env_vars(item) for item in value]
    return value


def _set_nested_value(d: dict[str, Any], path: list[str], value: Any) -> None:
    """Set a value in a nested dictionary using a path list.
    
    Creates intermediate dictionaries as needed if keys don't exist.
    
    Args:
        d: The dictionary to modify.
        path: List of keys representing the path to the target location.
        value: The value to set at the target location.
    """
    for key in path[:-1]:
        if key not in d:
            d[key] = {}
        d = d[key]
    d[path[-1]] = value


def apply_env_overrides(config: dict[str, Any]) -> dict[str, Any]:
    """Apply environment variable overrides using __ separator.

    Environment variables with the pattern SECTION__KEY can override
    nested configuration values. For example:
    - SERVER__PORT=9000 sets server.port to 9000
    - DATABASE__URL=postgresql://... sets database.url
    - SERVER__CORS__ORIGINS='["http://example.com"]' sets server.cors.origins

    Values are parsed as JSON if possible, otherwise treated as strings.

    Args:
        config: The configuration dictionary to modify.

    Returns:
        The modified configuration dictionary with overrides applied.
    """
    logger.debug("Applying environment variable overrides")
    overrides_count = 0
    for env_key, env_value in os.environ.items():
        for section in CONFIG_SECTIONS:
            if env_key.startswith(f"{section}__"):
                path = env_key.lower().split("__")
                try:
                    parsed_value = json.loads(env_value)
                except json.JSONDecodeError:
                    parsed_value = env_value
                _set_nested_value(config, path, parsed_value)
                logger.debug(f"Applied env override: {env_key}={parsed_value}")
                overrides_count += 1
                break
    if overrides_count > 0:
        logger.info(f"Applied {overrides_count} environment variable override(s)")
    return config


def get_active_profile() -> Optional[str]:
    """Get active profile from APP_PROFILE environment variable.
    
    Profiles allow loading different configuration files for different
    environments (e.g., 'dev', 'staging', 'production').
    
    Returns:
        The active profile name if set, None otherwise.
    """
    return os.getenv("APP_PROFILE")


def get_config_path() -> Path:
    """Get configuration file path based on environment settings.
    
    Resolution order:
    1. If APP_CONFIG_PATH is set:
       - With APP_PROFILE: use directory from APP_CONFIG_PATH with profile suffix
       - Without APP_PROFILE: use APP_CONFIG_PATH directly
    2. If APP_PROFILE is set: application-{profile}.yml
    3. Default: application.yml
    
    Returns:
        Path to the configuration file to load.
    """
    custom_path = os.getenv("APP_CONFIG_PATH")
    profile = get_active_profile()
    
    if custom_path:
        custom = Path(custom_path)
        if profile:
            # Use directory from APP_CONFIG_PATH with profile suffix
            return custom.parent / f"application-{profile}.yml"
        return custom
    
    if profile:
        return Path(__file__).parent / f"application-{profile}.yml"
    return Path(__file__).parent / "application.yml"


def load_config() -> AppConfig:
    """Load configuration from YAML file with interpolation and overrides.
    
    This function performs the following steps:
    1. Determines the configuration file path
    2. Loads the YAML file
    3. Applies environment variable interpolation (${VAR:default})
    4. Applies environment variable overrides (APP__SECTION__KEY)
    5. Validates the configuration using Pydantic models
    
    Returns:
        Validated AppConfig instance.
        
    Raises:
        FileNotFoundError: If the configuration file does not exist.
        yaml.YAMLError: If the YAML file is malformed.
        pydantic.ValidationError: If the configuration fails validation.
    """
    config_path = get_config_path()
    logger.info(f"Loading configuration from {config_path}")

    if not config_path.exists():
        logger.error(f"Config file not found: {config_path}")
        raise FileNotFoundError(f"Config file not found: {config_path}")

    # Load YAML
    logger.debug(f"Loading YAML file: {config_path}")
    with open(config_path, 'r') as f:
        raw_config = yaml.safe_load(f) or {}

    # Apply interpolation
    logger.debug("Applying environment variable interpolation")
    config = interpolate_env_vars(raw_config)

    # Apply env overrides
    logger.debug("Applying environment variable overrides")
    config = apply_env_overrides(config)

    # Validate with Pydantic
    validated_config = AppConfig(**config)
    logger.info(f"Configuration loaded successfully from {config_path}")
    return validated_config


def print_config(config: AppConfig, config_path: Path) -> None:
    """Print configuration details for debugging.

    Args:
        config: The loaded AppConfig instance.
        config_path: Path to the loaded config file.
    """
    logger.debug(f"Printing configuration from {config_path}")
    import sys
    print("\n" + "=" * 60, file=sys.stderr)
    print("Configuration Loaded", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    print(f"Config file: {config_path}", file=sys.stderr)
    print("-" * 60, file=sys.stderr)
    print("server:", file=sys.stderr)
    print(f"  host: {config.server.host}", file=sys.stderr)
    print(f"  port: {config.server.port}", file=sys.stderr)
    print("  cors:", file=sys.stderr)
    print(f"    origins: {config.server.cors.origins}", file=sys.stderr)
    print(f"    allow_credentials: {config.server.cors.allow_credentials}", file=sys.stderr)
    print(f"    allow_methods: {config.server.cors.allow_methods}", file=sys.stderr)
    print(f"    allow_headers: {config.server.cors.allow_headers}", file=sys.stderr)
    print("database:", file=sys.stderr)
    print(f"  url: {config.database.url}", file=sys.stderr)
    print(f"  echo: {config.database.echo}", file=sys.stderr)
    print("logging:", file=sys.stderr)
    print(f"  enabled: {config.logging.enabled}", file=sys.stderr)
    print(f"  level: {config.logging.level}", file=sys.stderr)
    print(f"  dir: {config.logging.dir}", file=sys.stderr)
    print(f"  format: {config.logging.format}", file=sys.stderr)
    print(f"  date_format: {config.logging.date_format}", file=sys.stderr)
    print("projects:", file=sys.stderr)
    print(f"  root: {config.projects.root}", file=sys.stderr)
    print("=" * 60 + "\n", file=sys.stderr)


@lru_cache(maxsize=1)
def get_config() -> AppConfig:
    """Get cached configuration instance.

    Uses LRU cache to ensure configuration is only loaded once per process.
    Subsequent calls return the same cached instance.

    Returns:
        Cached AppConfig instance.
    """
    config_path = get_config_path()
    config = load_config()
    print_config(config, config_path)
    logger.info("Returning cached configuration")
    return config


def reset_config_cache() -> None:
    """Reset configuration cache.
    
    Clears the LRU cache, forcing the next call to get_config()
    to reload the configuration from the file.
    
    This is primarily useful for testing scenarios where you need
    to test with different configuration files or environment variables.
    """
    get_config.cache_clear()


# Module exports
__all__ = [
    "AppConfig",
    "ServerConfig", 
    "DatabaseConfig",
    "CorsConfig",
    "LoggingConfig",
    "ProjectsConfig",
    "get_config",
    "reset_config_cache",
    "load_config",
    "get_config_path",
    "print_config",
]
