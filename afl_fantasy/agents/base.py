"""Base agent class using Anthropic API."""
import anthropic
from afl_fantasy.config import ANTHROPIC_API_KEY, SONNET, HAIKU


class BaseAgent:
    def __init__(self, model: str = SONNET):
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        self.model = model

    def ask(self, system: str, user: str, max_tokens: int = 2048) -> str:
        msg = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return msg.content[0].text
