from __future__ import annotations

from typing import TYPE_CHECKING

from .base import Translator
from .factory import create_translator

if TYPE_CHECKING:
    from ..config import Config


class TranslatorService:
    """Config-aware translator that lazily creates its backend.

    Reads all translation settings directly from *config* at call time.
    When the config is saved the cached backend is discarded so the next
    call to :meth:`translate` picks up the new settings.
    """

    def __init__(self, config: Config) -> None:
        self._config = config
        self._backend: Translator | None = None
        config.subscribe(self._on_config_changed)

    def translate(self, text: str) -> str:
        if self._backend is None:
            self._backend = self._create_backend()
        return self._backend.translate(text, self._config.translate_language)

    def _create_backend(self) -> Translator:
        cfg = self._config
        if cfg.translate_provider == "anthropic":
            api_key = cfg.anthropic_api_key
        elif cfg.translate_provider == "deepl":
            api_key = cfg.deepl_api_key
        else:
            raise ValueError(f"Unknown translator provider: {cfg.translate_provider!r}")
        return create_translator(
            provider=cfg.translate_provider,
            model=cfg.translate_model,
            max_tokens=cfg.translate_max_tokens,
            api_key=api_key,
        )

    def _on_config_changed(self) -> None:
        self._backend = None
