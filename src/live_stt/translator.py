import logging
import os

import anthropic
from dotenv import load_dotenv

log = logging.getLogger(__name__)


class Translator:
    def __init__(self):
        load_dotenv()
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not set. "
                "Set it in environment or in a .env file."
            )
        self._client = anthropic.Anthropic(api_key=api_key)

    def translate(self, text: str, target_language: str) -> str:
        log.debug("Translating to %s: %s", target_language, text)
        response = self._client.messages.create(
            model="claude-3-5-haiku-latest",
            max_tokens=1024,
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
