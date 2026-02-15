"""Claude API Client for BossHelp."""

from anthropic import Anthropic
from functools import lru_cache
from app.config import get_settings


class ClaudeClient:
    """Claude Sonnet 4 client for answer generation."""

    MODEL = "claude-sonnet-4-20250514"
    MAX_TOKENS_BASIC = 500
    MAX_TOKENS_EXPANDED = 1200

    def __init__(self):
        settings = get_settings()
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    def generate_answer(
        self,
        system_prompt: str,
        user_message: str,
        expanded: bool = False,
    ) -> str:
        """
        Generate an answer using Claude.

        Args:
            system_prompt: System prompt with rules and context
            user_message: User's question with retrieved chunks
            expanded: Whether to generate expanded answer (~800 chars)

        Returns:
            Generated answer text
        """
        max_tokens = self.MAX_TOKENS_EXPANDED if expanded else self.MAX_TOKENS_BASIC

        response = self.client.messages.create(
            model=self.MODEL,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_message}
            ],
        )

        return response.content[0].text

    def generate_answer_stream(
        self,
        system_prompt: str,
        user_message: str,
        expanded: bool = False,
    ):
        """
        Generate an answer using Claude with streaming.

        Yields:
            Text chunks as they are generated
        """
        max_tokens = self.MAX_TOKENS_EXPANDED if expanded else self.MAX_TOKENS_BASIC

        with self.client.messages.stream(
            model=self.MODEL,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_message}
            ],
        ) as stream:
            for text in stream.text_stream:
                yield text


@lru_cache()
def get_claude_client() -> ClaudeClient:
    """Get ClaudeClient singleton."""
    return ClaudeClient()
