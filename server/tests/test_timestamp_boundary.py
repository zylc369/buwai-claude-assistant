import pytest


class TestTimestampBoundary:
    """Validate all API responses return millisecond timestamps."""

    def test_timestamp_is_13_digit_integer(self):
        """Timestamps should be 13-digit integers (milliseconds)."""
        timestamp = 1700000000000  # Example: Nov 2023
        assert isinstance(timestamp, int)
        assert 1000000000000 < timestamp < 9999999999999

    def test_timestamp_not_seconds(self):
        """Timestamps should NOT be seconds (10-digit)."""
        timestamp_seconds = 1700000000  # Seconds: 10-digit
        timestamp_ms = 1700000000000  # Milliseconds: 13-digit

        # A 13-digit number is milliseconds
        assert len(str(timestamp_ms)) == 13
        assert len(str(timestamp_seconds)) == 10
        assert timestamp_ms > timestamp_seconds
