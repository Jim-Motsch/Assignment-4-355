"""Groq client (open models hosted on the Groq API)."""
import os

from dotenv import load_dotenv
from groq import Groq

from src.models.base import LLMClient

load_dotenv()


class GroqClient(LLMClient):
    """Sends prompts to a model on Groq and returns the text reply."""

    name = "groq"
    max_lines = 250  # free tier: 8k tokens/minute

    def __init__(self, model: str = "openai/gpt-oss-120b"):
        self.model = model
        self.client = Groq(api_key=os.environ["GROQ_API_KEY"])

    def send(self, system_prompt: str, user_prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=0,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response.choices[0].message.content


if __name__ == "__main__":
    print(GroqClient().send("Reply in one short sentence.", "Say hello."))