import pytest
import time
from utils.timestamp import get_timestamp_ms


class TestGetTimestampMs:
    def test_returns_integer(self):
        result = get_timestamp_ms()
        assert isinstance(result, int)

    def test_returns_milliseconds_13_digits(self):
        result = get_timestamp_ms()
        assert 1000000000000 < result < 9999999999999

    def test_consistent_rapid_calls(self):
        results = [get_timestamp_ms() for _ in range(10)]
        assert all(r == results[0] for r in results)

    def test_increases_over_time(self):
        first = get_timestamp_ms()
        time.sleep(0.01)
        second = get_timestamp_ms()
        assert second >= first

    def test_approximately_correct(self):
        expected = int(time.time() * 1000)
        result = get_timestamp_ms()
        assert abs(result - expected) < 100
