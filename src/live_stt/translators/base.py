from abc import ABC, abstractmethod


class Translator(ABC):
    """Interface that every translator backend must implement."""

    @abstractmethod
    def translate(self, text: str, target_language: str) -> str:
        """Translate *text* into *target_language* and return the result."""
