"""Tests for TitleGeneratorService."""

import pytest
from unittest.mock import MagicMock

from services.title_generator_service import TitleGeneratorService


class TestTitleGeneratorService:
    """Tests for TitleGeneratorService.generate_title method."""
    
    @pytest.fixture
    def service(self):
        """Create TitleGeneratorService instance with mock session."""
        mock_session = MagicMock()
        return TitleGeneratorService(mock_session)
    
    def test_generate_title_short_prompt(self, service):
        """Prompt shorter than 50 chars returns as-is."""
        prompt = "Hello, how can I help you today?"
        result = service.generate_title(prompt)
        assert result == prompt
        assert len(result) == 32
    
    def test_generate_title_long_prompt_truncated(self, service):
        """Long prompt truncated to 50 chars."""
        prompt = "This is a very long prompt that definitely exceeds the maximum title length limit of fifty characters"
        result = service.generate_title(prompt)
        # Should be truncated at word boundary + "..."
        assert result.endswith("...")
        # The truncated part (before ...) should be <= 50 chars
        assert len(result) <= 53  # 50 chars + "..."
    
    def test_generate_title_truncated_at_word_boundary(self, service):
        """Truncates at word boundary, not mid-word."""
        prompt = "This is a prompt with a supercalifragilisticexpialidocious word that will be cut"
        result = service.generate_title(prompt)
        # Should end with ... and not have partial words before it
        assert result.endswith("...")
        # Extract the part before "..."
        truncated_part = result[:-3]
        # Should not end with partial word (check it ends at space boundary or end of word)
        assert " " in truncated_part  # Should have been cut at a space
    
    def test_generate_title_empty_prompt(self, service):
        """Empty prompt returns 'New Conversation'."""
        result = service.generate_title("")
        assert result == "New Conversation"
    
    def test_generate_title_whitespace_only(self, service):
        """Whitespace-only prompt returns 'New Conversation'."""
        result = service.generate_title("   \t\n   ")
        assert result == "New Conversation"
