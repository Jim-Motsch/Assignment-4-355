"""Claude client (Anthropic API)."""
import os

from anthropic import Anthropic
from dotenv import load_dotenv

from src.models.base import LLMClient

load_dotenv()


class ClaudeClient(LLMClient):
    """Sends prompts to a Claude model and returns the text reply."""

    name = "claude"

    def __init__(self, model: str = "claude-sonnet-5-5"):
        self.model = model
        self.client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    def send(self, system_prompt: str, user_prompt: str) -> str:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        if response.stop_reason == "refusal":
            raise RuntimeError(f"Claude declined the request: {response.stop_details}")
        # Thinking blocks can come before the text, so content[0] isn't always text.
        return "".join(b.text for b in response.content if b.type == "text")


if __name__ == "__main__":
    print(ClaudeClient().send("Reply in one short sentence.", "Say hello."))