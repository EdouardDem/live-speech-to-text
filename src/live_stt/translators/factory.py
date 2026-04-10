from __future__ import annotations

from .base import Translator


def create_translator(provider: str, **kwargs) -> Translator:
    """Instantiate a translator backend by provider name.

    Supported providers: ``anthropic``, ``deepl``.
    """
    name = provider.strip().lower()

    if name == "anthropic":
        from .anthropic import AnthropicTranslator
        return AnthropicTranslator(**kwargs)

    if name == "deepl":
        from .deepl import DeepLTranslator
        return DeepLTranslator(**kwargs)

    raise ValueError(
        f"Unknown translator provider: {provider!r}. "
        f"Supported providers: anthropic, deepl."
    )

