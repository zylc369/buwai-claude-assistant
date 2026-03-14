"""UUIDv7 generator utility."""

from uuid7 import create
from uuid import UUID


def generate_uuidv7() -> str:
    """Generate a time-sortable UUIDv7 string.
    
    Returns:
        UUIDv7 string in format "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
    """
    return str(create())


def extract_timestamp(uuid_str: str) -> int:
    """Extract Unix timestamp (milliseconds) from a UUIDv7 string.
    
    Args:
        uuid_str: UUIDv7 string.
        
    Returns:
        Unix timestamp in milliseconds.
    """
    from uuid7 import time
    from datetime import datetime, UTC
    
    uuid_obj = UUID(uuid_str)
    dt = time(uuid_obj)
    return int(dt.timestamp() * 1000)