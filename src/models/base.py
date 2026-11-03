"""Common interface for every LLM provider used in the pipeline."""
from abc import ABC, abstractmethod


class LLMClient(ABC):
    """Base class for all model clients.

    The scanner and patcher only talk to this interface, so they work the
    same way no matter which model is plugged in.
    """

    name: str = "base"

    @abstractmethod
    def send(self, system_prompt: str, user_prompt: str) -> str:
        """Send prompts to the model and return its raw text reply."""
        raise NotImplementedError