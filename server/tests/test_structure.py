"""Test backend project structure and dependencies."""

import sys
from pathlib import Path

import pytest


def test_database_directory_exists():
    """Test that database directory exists with __init__.py."""
    db_dir = Path(__file__).parent.parent / "database"
    assert db_dir.exists(), "Database directory should exist"
    assert db_dir.is_dir(), "Database path should be a directory"


def test_database_init_exists():
    """Test that database/__init__.py exists and is readable."""
    db_init = Path(__file__).parent.parent / "database" / "__init__.py"
    assert db_init.exists(), "database/__init__.py should exist"
    assert db_init.is_file(), "database/__init__.py should be a file"


def test_routers_directory_exists():
    """Test that routers directory exists with __init__.py."""
    routers_dir = Path(__file__).parent.parent / "routers"
    assert routers_dir.exists(), "Routers directory should exist"
    assert routers_dir.is_dir(), "Routers path should be a directory"


def test_routers_init_exists():
    """Test that routers/__init__.py exists and is readable."""
    routers_init = Path(__file__).parent.parent / "routers" / "__init__.py"
    assert routers_init.exists(), "routers/__init__.py should exist"
    assert routers_init.is_file(), "routers/__init__.py should be a file"


def test_services_directory_exists():
    """Test that services directory exists with __init__.py."""
    services_dir = Path(__file__).parent.parent / "services"
    assert services_dir.exists(), "Services directory should exist"
    assert services_dir.is_dir(), "Services path should be a directory"


def test_services_init_exists():
    """Test that services/__init__.py exists and is readable."""
    services_init = Path(__file__).parent.parent / "services" / "__init__.py"
    assert services_init.exists(), "services/__init__.py should exist"
    assert services_init.is_file(), "services/__init__.py should be a file"


def test_repositories_directory_exists():
    """Test that repositories directory exists with __init__.py."""
    repos_dir = Path(__file__).parent.parent / "repositories"
    assert repos_dir.exists(), "Repositories directory should exist"
    assert repos_dir.is_dir(), "Repositories path should be a directory"


def test_repositories_init_exists():
    """Test that repositories/__init__.py exists and is readable."""
    repos_init = Path(__file__).parent.parent / "repositories" / "__init__.py"
    assert repos_init.exists(), "repositories/__init__.py should exist"
    assert repos_init.is_file(), "repositories/__init__.py should be a file"


def test_database_module_importable():
    """Test that database module can be imported."""
    sys.path.insert(0, str(Path(__file__).parent.parent))
    try:
        import database
        assert database is not None
    except ImportError as e:
        pytest.fail(f"Failed to import database module: {e}")


def test_routers_module_importable():
    """Test that routers module can be imported."""
    sys.path.insert(0, str(Path(__file__).parent.parent))
    try:
        import routers
        assert routers is not None
    except ImportError as e:
        pytest.fail(f"Failed to import routers module: {e}")


def test_services_module_importable():
    """Test that services module can be imported."""
    sys.path.insert(0, str(Path(__file__).parent.parent))
    try:
        import services
        assert services is not None
    except ImportError as e:
        pytest.fail(f"Failed to import services module: {e}")


def test_repositories_module_importable():
    """Test that repositories module can be imported."""
    sys.path.insert(0, str(Path(__file__).parent.parent))
    try:
        import repositories
        assert repositories is not None
    except ImportError as e:
        pytest.fail(f"Failed to import repositories module: {e}")


def test_structure_consistency():
    """Test that all required modules exist and are in the expected location."""
    base_path = Path(__file__).parent.parent
    required_dirs = ["database", "routers", "services", "repositories"]
    required_files = {
        "database": ["__init__.py"],
        "routers": ["__init__.py"],
        "services": ["__init__.py"],
        "repositories": ["__init__.py"],
    }

    for dir_name in required_dirs:
        dir_path = base_path / dir_name
        assert dir_path.exists(), f"{dir_name} directory should exist"
        assert dir_path.is_dir(), f"{dir_name} should be a directory"

        for filename in required_files[dir_name]:
            file_path = dir_path / filename
            assert file_path.exists(), f"{dir_name}/{filename} should exist"
            assert file_path.is_file(), f"{dir_name}/{filename} should be a file"


def test_fastapi_dependency_exists():
    """Test that FastAPI dependency is in requirements.txt."""
    requirements_path = Path(__file__).parent.parent / "requirements.txt"
    assert requirements_path.exists(), "requirements.txt should exist"

    with open(requirements_path, "r") as f:
        content = f.read()
        assert "fastapi" in content.lower(), "FastAPI should be in requirements.txt"


def test_uvicorn_dependency_exists():
    """Test that uvicorn dependency is in requirements.txt."""
    requirements_path = Path(__file__).parent.parent / "requirements.txt"
    assert requirements_path.exists(), "requirements.txt should exist"

    with open(requirements_path, "r") as f:
        content = f.read()
        assert "uvicorn" in content.lower(), "Uvicorn should be in requirements.txt"


def test_sqlalchemy_dependency_exists():
    """Test that SQLAlchemy dependency is in requirements.txt."""
    requirements_path = Path(__file__).parent.parent / "requirements.txt"
    assert requirements_path.exists(), "requirements.txt should exist"

    with open(requirements_path, "r") as f:
        content = f.read()
        assert "sqlalchemy" in content.lower(), "SQLAlchemy should be in requirements.txt"


def test_aiosqlite_dependency_exists():
    """Test that aiosqlite dependency is in requirements.txt."""
    requirements_path = Path(__file__).parent.parent / "requirements.txt"
    assert requirements_path.exists(), "requirements.txt should exist"

    with open(requirements_path, "r") as f:
        content = f.read()
        assert "aiosqlite" in content.lower(), "aiosqlite should be in requirements.txt"


def test_alembic_dependency_exists():
    """Test that alembic dependency is in requirements.txt."""
    requirements_path = Path(__file__).parent.parent / "requirements.txt"
    assert requirements_path.exists(), "requirements.txt should exist"

    with open(requirements_path, "r") as f:
        content = f.read()
        assert "alembic" in content.lower(), "alembic should be in requirements.txt"

