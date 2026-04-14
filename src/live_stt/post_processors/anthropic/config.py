"""Default configuration values for the Anthropic post-processor."""

DEFAULTS: dict[str, object] = {
    "prompt": (
        "Translate the following text to English. "
        "Return only the translation:\n\n{INPUT}"
    ),
    "model": "claude-haiku-4-5-20251001",
    "max_tokens": 1024,
}
