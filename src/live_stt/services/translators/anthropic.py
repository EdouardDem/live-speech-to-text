import logging
import os

import anthropic
from dotenv import load_dotenv

from .base import Translator

log = logging.getLogger(__name__)


class AnthropicTranslator(Translator):
    """Translation backend using the Anthropic (Claude) API."""

    def __init__(self, model: str, max_tokens: int):
        load_dotenv()
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not set. "
                "Set it in environment or in a .env file."
            )
        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model
        self._max_tokens = max_tokens

    def translate(self, text: str, target_language: str) -> str:
        log.debug("Translating to %s: %s", target_language, text)
        response = self._client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Translate the following text to {target_language}. "
                        f"Return only the translation, nothing else:\n\n{text}"
                    ),
                }
            ],
        )
        translated = response.content[0].text.strip()
        log.debug("Translation result: %s", translated)
        return translated
