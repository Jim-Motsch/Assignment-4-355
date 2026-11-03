"""Gemini client (Google AI Studio API)."""
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

from src.models.base import LLMClient

load_dotenv()  # reads GEMINI_API_KEY from .env


class GeminiClient(LLMClient):
    """Sends prompts to a Gemini model and returns the text reply."""

    name = "gemini"

    def __init__(self, model: str = "gemini-3.5-flash-lite"):
        self.model = model
        self.client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

    def send(self, system_prompt: str, user_prompt: str) -> str:
        response = self.client.models.generate_content(
            model=self.model,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0,  # same input -> same output, easier to compare
            ),
        )
        return response.text


if __name__ == "__main__":
    # Quick smoke test: python -m src.models.gemini
    print(GeminiClient().send("Reply in one short sentence.", "Say hello."))