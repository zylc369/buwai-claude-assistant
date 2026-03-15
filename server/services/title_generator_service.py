"""Title generator service for creating session titles from prompts."""

from sqlalchemy.ext.asyncio import AsyncSession
from logger import get_logger

logger = get_logger(__name__)


class TitleGeneratorService:
    """Generate session titles from user prompts using simple heuristics."""
    
    MAX_TITLE_LENGTH = 50
    
    def __init__(self, session: AsyncSession):
        """Initialize TitleGeneratorService.
        
        Args:
            session: SQLAlchemy async session (for future LLM-based generation)
        """
        self.session = session
    
    def generate_title(self, prompt: str) -> str:
        """Generate a session title from the first user prompt.
        
        Uses simple heuristic: first 50 chars, truncated to last complete word.
        
        Args:
            prompt: The user's first prompt in the session
            
        Returns:
            Generated title string (max 50 chars)
        """
        if not prompt or not prompt.strip():
            return "New Conversation"
        
        # Clean the prompt
        cleaned = prompt.strip()
        
        # If short enough, use as-is
        if len(cleaned) <= self.MAX_TITLE_LENGTH:
            return cleaned
        
        # Truncate to max length
        truncated = cleaned[:self.MAX_TITLE_LENGTH]
        
        # Find last complete word (don't end mid-word)
        last_space = truncated.rfind(' ')
        if last_space > 0:
            truncated = truncated[:last_space]
        
        return truncated.strip() + "..."
