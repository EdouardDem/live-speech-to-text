import os

import deepl
from dotenv import load_dotenv

from .. import logger
from .base import Translator

log = logger.get(__name__)

# DeepL uses language codes, not language names.
# Map common language names to DeepL target language codes.
_LANGUAGE_MAP: dict[str, str] = {
    "bulgarian": "BG",
    "czech": "CS",
    "danish": "DA",
    "german": "DE",
    "greek": "EL",
    "english": "EN-US",
    "english (american)": "EN-US",
    "english (british)": "EN-GB",
    "spanish": "ES",
    "estonian": "ET",
    "finnish": "FI",
    "french": "FR",
    "hungarian": "HU",
    "indonesian": "ID",
    "italian": "IT",
    "japanese": "JA",
    "korean": "KO",
    "lithuanian": "LT",
    "latvian": "LV",
    "norwegian": "NB",
    "dutch": "NL",
    "polish": "PL",
    "portuguese": "PT-PT",
    "portuguese (brazilian)": "PT-BR",
    "romanian": "RO",
    "russian": "RU",
    "slovak": "SK",
    "slovenian": "SL",
    "swedish": "SV",
    "turkish": "TR",
    "ukrainian": "UK",
    "chinese": "ZH-HANS",
    "chinese (simplified)": "ZH-HANS",
    "chinese (traditional)": "ZH-HANT",
}


def _resolve_language_code(target_language: str) -> str:
    """Convert a human-readable language name to a DeepL language code."""
    key = target_language.strip().lower()
    if key in _LANGUAGE_MAP:
        return _LANGUAGE_MAP[key]
    # If it already looks like a code (e.g. "FR", "EN-US"), pass it through.
    return target_language.upper()


class DeepLTranslator(Translator):
    """Translation backend using the DeepL API."""

    def __init__(self, **_kwargs):
        load_dotenv()
        api_key = os.getenv("DEEPL_API_KEY")
        if not api_key:
            raise ValueError(
                "DEEPL_API_KEY not set. "
                "Set it in environment or in a .env file."
            )
        self._translator = deepl.Translator(api_key)

    def translate(self, text: str, target_language: str) -> str:
        lang_code = _resolve_language_code(target_language)
        log.debug("Translating to %s (%s): %s", target_language, lang_code, text)
        result = self._translator.translate_text(text, target_lang=lang_code)
        translated = result.text.strip()
        log.debug("Translation result: %s", translated)
        return translated
