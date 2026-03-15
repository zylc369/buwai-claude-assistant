"""Timestamp utility functions."""


def get_timestamp_ms() -> int:
    """Get current timestamp in milliseconds.
    
    Returns:
        Current Unix timestamp in milliseconds (13-digit integer).
    """
    import time
    return int(time.time() * 1000)
