import os

from ..base import PostProcessor, PostProcessorConfig
from ...services import logger

log = logger.get(__name__)

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

# Sorted language names for UI dropdowns.
LANGUAGE_NAMES: list[str] = sorted(
    {v: k.title() for k, v in _LANGUAGE_MAP.items()}.values()
)


def resolve_language_code(target_language: str) -> str:
    """Convert a human-readable language name to a DeepL language code."""
    key = target_language.strip().lower()
    if key in _LANGUAGE_MAP:
        return _LANGUAGE_MAP[key]
    return target_language.upper()


class DeepLProcessor(PostProcessor):
    """Post-processor that translates text via the DeepL API."""

    def __init__(self, cfg: PostProcessorConfig, api_key: str = "") -> None:
        super().__init__(cfg)
        import deepl  # lazy import

        key = api_key or os.getenv("DEEPL_API_KEY", "")
        if not key:
            raise ValueError(
                "DeepL API key not configured. "
                "Set it in Settings → API Keys or via DEEPL_API_KEY."
            )
        self._translator = deepl.Translator(key)

    def run(self, text: str) -> str:
        lang_code = resolve_language_code(self.cfg.target_language)
        log.debug(
            "[%s] → DeepL (%s / %s): %s…",
            self.cfg.name, self.cfg.target_language, lang_code, text[:60],
        )
        result = self._translator.translate_text(text, target_lang=lang_code)
        translated = result.text.strip()
        log.debug("[%s] ← %s…", self.cfg.name, translated[:80])
        return translated
